import os
import json
import requests
import datetime
from bs4 import BeautifulSoup
import csv
import traceback
import argparse
import sys

# Konfigurationspfade
CONFIG_DIR = "config"
CONFIG_FILE = os.path.join(CONFIG_DIR, "moodle_config.json")
OUTPUT_DIR = "moodle_kurse"

# Standardwerte
DEFAULT_CONFIG = {
    "moodle_url": "https://moodle.fh-campuswien.ac.at",
    "username": "",
    "password": "",
    "auto_sync": True,
    "last_sync": None,
    "course_count": 0,
    "assignment_count": 0,
    "overdue_count": 0
}

def ensure_dirs_exist():
    """Stelle sicher, dass alle benötigten Verzeichnisse existieren."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "kurse"), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "aufgaben"), exist_ok=True)

def load_config():
    """Lade Konfiguration aus der JSON-Datei oder erstelle Standardwerte."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        else:
            # Wenn keine Konfigurationsdatei existiert, erstelle eine mit Standardwerten
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"Fehler beim Laden der Konfiguration: {str(e)}")
        return DEFAULT_CONFIG

def save_config(config):
    """Speichere Konfiguration in JSON-Datei."""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Fehler beim Speichern der Konfiguration: {str(e)}")
        return False

def update_sync_results(course_count, assignment_count, overdue_count):
    """Aktualisiere die Synchronisierungsergebnisse in der Konfigurationsdatei."""
    config = load_config()
    config["last_sync"] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    config["course_count"] = course_count
    config["assignment_count"] = assignment_count
    config["overdue_count"] = overdue_count
    save_config(config)

def login_to_moodle(moodle_url, username, password):
    """Bei Moodle anmelden und Session zurückgeben."""
    session = requests.Session()
    
    # Anmeldeseite abrufen, um Tokens zu erhalten
    print("Rufe Login-Seite ab...")
    login_url = f"{moodle_url}/login/index.php"
    login_page = session.get(login_url)
    soup = BeautifulSoup(login_page.text, 'html.parser')
    
    # Login-Token suchen
    login_token_input = soup.find('input', {'name': 'logintoken'})
    if not login_token_input:
        print("Konnte kein Login-Token finden. Möglicherweise hat sich die Seite geändert.")
        return None
    
    login_token = login_token_input['value']
    print(f"Login-Token gefunden: {login_token}")
    
    # Anmeldedaten vorbereiten
    login_data = {
        'username': username,
        'password': password,
        'logintoken': login_token,
        'anchor': ''
    }
    
    # Anmeldung durchführen
    print("Sende Anmeldedaten...")
    response = session.post(login_url, data=login_data)
    
    # Überprüfen, ob die Anmeldung erfolgreich war
    if "loginerrormessage" in response.text:
        print("Anmeldung fehlgeschlagen. Überprüfen Sie Benutzername und Passwort.")
        return None
    
    # Prüfen, ob wir auf Dashboard weitergeleitet wurden
    if "/my/" in response.url or "Sie sind angemeldet als" in response.text or "You are logged in as" in response.text:
        print("Anmeldung erfolgreich!")
        # Speichere HTML für Debugging
        save_html_to_file(response.text, "dashboard.html")
        
        print(f"Aktuelle URL nach Login: {response.url}")
        return session
    else:
        print("Anmeldung möglicherweise fehlgeschlagen. Überprüfen Sie die Ausgabe.")
        save_html_to_file(response.text, "login_response.html")
        return None

def save_html_to_file(html_content, filename, subfolder=""):
    """Speichert HTML-Inhalt in eine Datei im Ausgabeordner."""
    # Erstelle den vollständigen Pfad
    if subfolder:
        folder_path = os.path.join(OUTPUT_DIR, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
    else:
        file_path = os.path.join(OUTPUT_DIR, filename)
    
    # Speichere die Datei
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return file_path

def get_courses(session, moodle_url):
    """Kurse von der Moodle-Plattform abrufen, der Navigationsstruktur folgend."""
    if not session:
        return []
    
    # Dashboard-Seite aufrufen
    dashboard_url = f"{moodle_url}/my/"
    print(f"Rufe Dashboard-Seite ab: {dashboard_url}")
    response = session.get(dashboard_url)
    
    # HTML zur Analyse speichern
    save_html_to_file(response.text, "dashboard.html")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Finde den "Meine Kurse" Link in der Navigation
    meine_kurse_link = None
    for link in soup.find_all('a'):
        if 'Meine Kurse' in link.text:
            meine_kurse_link = link.get('href')
            print(f"Meine Kurse Link gefunden: {meine_kurse_link}")
            break
    
    if not meine_kurse_link:
        print("Konnte 'Meine Kurse' Link nicht finden")
        return []
    
    # Navigiere zur "Meine Kurse" Seite
    print(f"Navigiere zu: {meine_kurse_link}")
    response = session.get(meine_kurse_link)
    
    save_html_to_file(response.text, "meine_kurse.html")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Sammle alle potenziellen Studiengänge/Kategorien (ignoriere "Hilfe zu Moodle")
    studiengang_links = []
    for link in soup.find_all('a'):
        link_text = link.text.strip()
        link_href = link.get('href')
        
        # Ignoriere leere Links und alles mit "Moodle"
        if not link_text or not link_href or "moodle" in link_text.lower():
            continue
        
        # Ignoriere Standard-Navigationselemente
        if "Dashboard" in link_text or "Website" in link_text or "Meine Kurse" in link_text:
            continue
            
        # Ignoriere Links, die nicht auf Moodle-Kurse oder -Kategorien verweisen könnten
        if not any(pattern in link_href for pattern in ['/course/', '/category/', '/user/']):
            continue
            
        print(f"Potenzieller Studiengang gefunden: {link_text}")
        studiengang_links.append({
            'name': link_text,
            'url': link_href
        })
    
    if not studiengang_links:
        print("Keine Studiengänge/Kategorien gefunden")
        return find_all_available_courses(soup)
    
    # Für jeden Studiengang suchen wir nach Kursen und Semestern
    all_courses = []
    
    for studiengang in studiengang_links:
        studiengang_name = clean_filename(studiengang['name'])
        print(f"\nNavigiere zu Studiengang: {studiengang['name']}")
        try:
            response = session.get(studiengang['url'])
            
            # Erstelle einen Ordner für den Studiengang
            save_html_to_file(response.text, f"{studiengang_name}.html", studiengang_name)
            
            studiengang_soup = BeautifulSoup(response.text, 'html.parser')
            
            # Suche nach Semestern oder direkt nach Kursen
            semester_links = []
            for link in studiengang_soup.find_all('a'):
                link_text = link.text.strip().lower()
                # Ignoriere Moodle-bezogene Links
                if "moodle" in link_text:
                    continue
                if any(term in link_text for term in ['semester', 'sommer', 'winter']):
                    semester_links.append({
                        'name': link.text.strip(),
                        'url': link.get('href')
                    })
                    print(f"Semester gefunden: {link.text.strip()}")
            
            if semester_links:
                # Wenn Semester gefunden wurden, navigiere zu jedem und sammle Kurse
                for semester in semester_links:
                    try:
                        semester_name = clean_filename(semester['name'])
                        print(f"Navigiere zu Semester: {semester['name']}")
                        sem_response = session.get(semester['url'])
                        
                        save_html_to_file(
                            sem_response.text, 
                            f"{semester_name}.html", 
                            os.path.join(studiengang_name, "semester")
                        )
                        
                        sem_soup = BeautifulSoup(sem_response.text, 'html.parser')
                        semester_courses = extract_courses_from_page(
                            sem_soup, 
                            f"{studiengang['name']} - {semester['name']}",
                            os.path.join(studiengang_name, "semester", semester_name)
                        )
                        all_courses.extend(semester_courses)
                    except Exception as e:
                        print(f"Fehler beim Navigieren zum Semester {semester['name']}: {str(e)}")
            else:
                # Wenn keine Semester gefunden wurden, suche direkt nach Kursen
                print("Keine Semester gefunden, suche direkt nach Kursen")
                studiengang_courses = extract_courses_from_page(
                    studiengang_soup, 
                    studiengang['name'],
                    studiengang_name
                )
                all_courses.extend(studiengang_courses)
        except Exception as e:
            print(f"Fehler beim Navigieren zum Studiengang {studiengang['name']}: {str(e)}")
    
    # Filtere Moodle-bezogene Kurse aus den Ergebnissen
    filtered_courses = [course for course in all_courses if not should_ignore_course(course['name'])]
    
    # Falls keine Kurse gefunden wurden, versuche einen allgemeinen Ansatz
    if not filtered_courses:
        print("\nKeine spezifischen Kurse gefunden, versuche allgemeine Suche")
        all_search_courses = find_all_available_courses(soup)
        filtered_courses = [course for course in all_search_courses if not should_ignore_course(course['name'])]
    
    if len(all_courses) != len(filtered_courses):
        print(f"\n{len(all_courses) - len(filtered_courses)} Moodle-bezogene Kurse wurden gefiltert.")
    
    return filtered_courses

def clean_filename(filename):
    """Bereinigt einen Dateinamen von unerlaubten Zeichen."""
    # Ersetze unerlaubte Zeichen durch Unterstrich
    import re
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def should_ignore_course(course_name):
    """Prüft, ob ein Kurs ignoriert werden sollte (z.B. Moodle-Tutorials)."""
    # Ignoriere alles, was "Moodle" im Namen enthält
    if "moodle" in course_name.lower():
        return True
    return False

def get_assignment_details(session, course):
    """Ruft die Details zu Aufgaben und Bewertungen eines Kurses ab."""
    print(f"\nPrüfe Aufgaben für: {course['name']}")
    
    try:
        # Besuche die Kursseite
        response = session.get(course['url'])
        course_soup = BeautifulSoup(response.text, 'html.parser')
        
        # Speichere die Kursseite
        course_name_safe = clean_filename(course['name'])
        save_html_to_file(response.text, f"{course_name_safe}.html", "kurse")
        
        assignments = []
        
        # METHODE 1: Direkte Suche nach Aufgaben auf der Kursseite
        print("Suche direkt nach Aufgaben auf der Kursseite...")
        for link in course_soup.find_all('a'):
            link_text = link.text.strip().lower()
            link_href = link.get('href', '')
            
            # Direkte Erkennung von Aufgaben anhand der Linktext
            if any(term in link_text for term in ['assignment', 'aufgabe', 'abgabe', 'learning', 'übung', 'distance']):
                assignment_name = link.text.strip()
                assignment_link = link_href
                
                if assignment_link and ('assign' in assignment_link or 'mod' in assignment_link):
                    print(f"Aufgabe direkt gefunden: {assignment_name}")
                    try:
                        print(f"Prüfe Details für Aufgabe: {assignment_name}")
                        assignment_response = session.get(assignment_link)
                        assignment_soup = BeautifulSoup(assignment_response.text, 'html.parser')
                        
                        # Speichere die Aufgabenseite
                        save_html_to_file(
                            assignment_response.text, 
                            f"{course_name_safe}_{clean_filename(assignment_name)}.html", 
                            "aufgaben"
                        )
                        
                        # Extrahiere Datumsangaben
                        due_date, opening_date, remaining_time = extract_assignment_dates(assignment_soup)
                        
                        # Debug-Ausgabe
                        print(f"  Öffnung: {opening_date}")
                        print(f"  Fällig: {due_date}")
                        print(f"  Verbleibende Zeit: {remaining_time}")
                        
                        # Überprüfen auf "überschritten"
                        is_overdue = False
                        if remaining_time and 'überschritten' in remaining_time.lower():
                            is_overdue = True
                            print(f"  ÜBERFÄLLIG erkannt!")
                        
                        assignments.append({
                            'name': assignment_name,
                            'url': assignment_link,
                            'opening_date': opening_date,
                            'due_date': due_date,
                            'remaining_time': remaining_time,
                            'is_overdue': is_overdue
                        })
                    except Exception as e:
                        print(f"Fehler beim Abrufen der Aufgabendetails: {str(e)}")
        
        # METHODE 2: Suche nach Bewertungen-Link und dessen Analyse
        if not assignments:
            print("Suche nach Bewertungen-Link...")
            bewertungen_link = None
            for link in course_soup.find_all('a'):
                if 'Bewertungen' in link.text:
                    bewertungen_link = link.get('href')
                    print(f"Bewertungen Link gefunden: {bewertungen_link}")
                    break
            
            # Wenn kein Bewertungen-Link gefunden wurde, suche nach alternativen Links
            if not bewertungen_link:
                print("Kein direkter Bewertungen-Link gefunden, suche Alternativen...")
                for link in course_soup.find_all('a'):
                    link_text = link.text.strip()
                    if any(term in link_text for term in ['Teilnehmer', 'Teilnehmer/innen', 'Participants', 'Grades', 'Bewertung', 'Assessment']):
                        bewertungen_link = link.get('href')
                        print(f"Alternativer Link gefunden: {link_text} -> {bewertungen_link}")
                        break
            
            if bewertungen_link:
                # Besuche die Bewertungen-Seite
                print(f"Navigiere zu: {bewertungen_link}")
                response = session.get(bewertungen_link)
                bewertungen_soup = BeautifulSoup(response.text, 'html.parser')
                
                # Speichere die Bewertungen-Seite
                save_html_to_file(response.text, f"{course_name_safe}_bewertungen.html", "kurse")
                
                # Suche nach Aufgabentiteln auf der Bewertungsseite
                print("Suche nach Aufgaben auf der Bewertungsseite...")
                for element in bewertungen_soup.find_all(['a', 'span', 'div', 'tr', 'td']):
                    element_text = element.text.strip().lower()
                    
                    # Erweiterte Aufgabenerkennung
                    if element_text and any(term in element_text for term in 
                        ['assignment', 'aufgabe', 'abgabe', 'learning', 'distance', 'übung', 'geöffnet', 'fällig']):
                        
                        # Bestimme den tatsächlichen Namen der Aufgabe
                        assignment_name = element.text.strip()
                        assignment_link = element.get('href') if element.name == 'a' else None
                        
                        # Wenn der Link nicht direkt gefunden wurde, suche nach einem nahegelegenen Link
                        if not assignment_link and element.name in ['span', 'div', 'td']:
                            # Suche nach einem Link innerhalb des Elements
                            link_in_element = element.find('a')
                            if link_in_element:
                                assignment_link = link_in_element.get('href')
                                assignment_name = link_in_element.text.strip() or assignment_name
                            else:
                                # Suche nach einem Link in den Geschwisterelementen
                                siblings = list(element.parent.find_all('a'))
                                if siblings:
                                    assignment_link = siblings[0].get('href')
                        
                        # Wenn wir einen Link haben, folge diesem zur Detailseite
                        if assignment_link:
                            print(f"Aufgabe in Bewertung gefunden: {assignment_name}")
                            try:
                                assignment_response = session.get(assignment_link)
                                assignment_soup = BeautifulSoup(assignment_response.text, 'html.parser')
                                
                                # Speichere die Aufgabenseite
                                save_html_to_file(
                                    assignment_response.text, 
                                    f"{course_name_safe}_{clean_filename(assignment_name)}.html", 
                                    "aufgaben"
                                )
                                
                                # Extrahiere Datumsangaben
                                due_date, opening_date, remaining_time = extract_assignment_dates(assignment_soup)
                                
                                # Debug-Ausgabe
                                print(f"  Öffnung: {opening_date}")
                                print(f"  Fällig: {due_date}")
                                print(f"  Verbleibende Zeit: {remaining_time}")
                                
                                # Überprüfen auf "überschritten"
                                is_overdue = False
                                if remaining_time and 'überschritten' in remaining_time.lower():
                                    is_overdue = True
                                    print(f"  ÜBERFÄLLIG erkannt!")
                                
                                # Prüfe, ob diese Aufgabe bereits erfasst wurde
                                if not any(a['name'] == assignment_name for a in assignments):
                                    assignments.append({
                                        'name': assignment_name,
                                        'url': assignment_link,
                                        'opening_date': opening_date,
                                        'due_date': due_date,
                                        'remaining_time': remaining_time,
                                        'is_overdue': is_overdue
                                    })
                            except Exception as e:
                                print(f"Fehler beim Abrufen der Aufgabendetails: {str(e)}")
        
        # METHODE 3: Suche nach speziellen Aktivitätsblöcken im Kurs
        if not assignments:
            print("Suche nach Aktivitätsblöcken im Kurs...")
            activity_sections = course_soup.select('.activity')
            if activity_sections:
                print(f"Gefunden: {len(activity_sections)} Aktivitätsblöcke")
                for activity in activity_sections:
                    activity_link = activity.find('a')
                    if activity_link:
                        activity_name = activity_link.text.strip()
                        activity_url = activity_link.get('href')
                        
                        # Prüfe, ob es sich um eine Aufgabe handeln könnte
                        if any(term in activity_name.lower() for term in ['assignment', 'aufgabe', 'learning', 'abgabe', 'übung']):
                            print(f"Aktivität gefunden: {activity_name}")
                            try:
                                activity_response = session.get(activity_url)
                                activity_soup = BeautifulSoup(activity_response.text, 'html.parser')
                                
                                # Speichere die Aktivitätsseite
                                save_html_to_file(
                                    activity_response.text, 
                                    f"{course_name_safe}_{clean_filename(activity_name)}.html", 
                                    "aufgaben"
                                )
                                
                                # Extrahiere Datumsangaben
                                due_date, opening_date, remaining_time = extract_assignment_dates(activity_soup)
                                
                                # Überprüfen auf "überschritten"
                                is_overdue = False
                                if remaining_time and 'überschritten' in remaining_time.lower():
                                    is_overdue = True
                                    print(f"  ÜBERFÄLLIG erkannt!")
                                
                                assignments.append({
                                    'name': activity_name,
                                    'url': activity_url,
                                    'opening_date': opening_date,
                                    'due_date': due_date,
                                    'remaining_time': remaining_time,
                                    'is_overdue': is_overdue
                                })
                            except Exception as e:
                                print(f"Fehler beim Abrufen der Aktivitätsdetails: {str(e)}")
        
        print(f"Gefundene Aufgaben für Kurs '{course['name']}': {len(assignments)}")
        return {
            'has_assignments': len(assignments) > 0,
            'assignments': assignments
        }
    
    except Exception as e:
        print(f"Fehler beim Prüfen der Aufgaben: {str(e)}")
        return {
            'has_assignments': False,
            'assignments': [],
            'error': str(e)
        }

def extract_assignment_dates(soup):
    """Extrahiert Öffnungs-, Fälligkeits- und verbleibende Zeit aus der Aufgabenseite."""
    due_date = None
    opening_date = None
    remaining_time = None
    
    # Debug: HTML für manuelle Analyse speichern
    debug_html = str(soup)
    if 'verbleibende zeit' in debug_html.lower() or 'überschritten' in debug_html.lower():
        print("*** HINWEIS: Zeitangaben zur Abgabe in HTML gefunden! ***")
    
    # Suche nach spezifischen Elementen, die in Moodle üblicherweise Zeitangaben enthalten
    date_elements = []
    
    # Suche 1: Nach Tabellenzellen
    for row in soup.select('tr'):
        header_cell = row.find('th')
        data_cell = row.find('td')
        if header_cell and data_cell:
            header_text = header_cell.text.strip().lower()
            data_text = data_cell.text.strip()
            date_elements.append((header_text, data_text))
    
    # Suche 2: Nach beschrifteten Zeitangaben
    for element in soup.find_all(['div', 'td', 'span', 'p', 'li', 'h4']):
        text = element.text.strip()
        
        # Suche nach Zeilen wie "Öffnung: [Datum]" oder "Fällig: [Datum]"
        if ':' in text and len(text) < 100:  # Begrenze auf kurze Texte
            date_elements.append((text.lower(), text))
    
    # Suche 3: Nach speziellen Moodle-Elementen für Zeitangaben
    for element in soup.select('.cell.c1.lastcol'):
        text = element.text.strip()
        if text:
            date_elements.append(('zeit', text))
    
    # Verarbeite die gefundenen Elemente
    for key, value in date_elements:
        # Öffnungsdatum
        if any(term in key for term in ['geöffnet', 'öffnung', 'beginn', 'available', 'von', 'from']):
            opening_date = value
            print(f"Öffnungsdatum gefunden: {value}")
        
        # Fälligkeitsdatum
        elif any(term in key for term in ['fällig', 'abgabe', 'due', 'bis', 'until', 'submission']):
            due_date = value
            print(f"Fälligkeitsdatum gefunden: {value}")
        
        # Verbleibende Zeit
        elif any(term in key for term in ['verbleibende zeit', 'überschritten', 'time remaining', 'verbleibend', 'remaining']):
            remaining_time = value
            print(f"Verbleibende Zeit gefunden: {value}")
    
    # Wenn die spezifische Suche nichts findet, suche nach typischen Datumsformaten und Beschriftungen
    if not (due_date or opening_date or remaining_time):
        for element in soup.find_all(['div', 'td', 'span', 'p']):
            text = element.text.strip().lower()
            
            # Suche nach typischen Zeitformaten wie DD.MM.YYYY oder überschritten seit X Tagen
            if any(pattern in text for pattern in ['.20', '.202', 'überschritten', 'verbleibend']):
                if 'geöffnet' in text or 'öffnung' in text or 'beginn' in text:
                    opening_date = element.text.strip()
                elif 'fällig' in text or 'abgabe' in text or 'due' in text:
                    due_date = element.text.strip()
                elif 'verbleibende zeit' in text or 'überschritten' in text:
                    remaining_time = element.text.strip()
    
    # Extrahiere die Zeitangabe aus verbleibender Zeit
    if remaining_time and 'überschritten' in remaining_time.lower():
        print("!!! ÜBERFÄLLIGE AUFGABE GEFUNDEN !!!")
    
    return due_date, opening_date, remaining_time

def find_all_available_courses(soup):
    """Versucht, alle verfügbaren Kurse auf der aktuellen Seite zu finden."""
    courses = []
    
    # Versuche mit verschiedenen Selektoren
    # 1. Versuche die Kurskarten zu finden
    course_cards = soup.select('div.course-card')
    if course_cards:
        print(f"Gefunden: {len(course_cards)} Kurskarten")
        for card in course_cards:
            link = card.find('a')
            if link:
                course_name = link.text.strip()
                course_url = link.get('href')
                courses.append({
                    'name': course_name,
                    'url': course_url
                })
    
    # 2. Versuche die Kurslinks in der Kursliste zu finden
    if not courses:
        course_list_items = soup.select('li.courselist-course')
        if course_list_items:
            print(f"Gefunden: {len(course_list_items)} Kurslisteneinträge")
            for item in course_list_items:
                link = item.find('a')
                if link:
                    course_name = link.text.strip()
                    course_url = link.get('href')
                    courses.append({
                        'name': course_name,
                        'url': course_url
                    })
    
    # 3. Allgemeiner Versuch: Suche nach allen Links, die auf Kurse verweisen könnten
    if not courses:
        for link in soup.find_all('a'):
            href = link.get('href', '')
            # Typische Moodle-Kurs-URLs enthalten "course/view.php?id="
            if 'course/view.php?id=' in href:
                course_name = link.text.strip()
                course_url = href
                if course_name and not any(c['url'] == course_url for c in courses):
                    courses.append({
                        'name': course_name,
                        'url': course_url
                    })
    
    print(f"Insgesamt {len(courses)} Kurse mit allgemeiner Suche gefunden")
    return courses

def extract_courses_from_page(soup, semester_name, subfolder=""):
    """Extrahiert Kurse aus einer Semesterseite."""
    courses = []
    
    # Versuche zunächst, spezifische Kursblöcke zu finden
    course_sections = soup.select('li.section')
    
    for section in course_sections:
        section_name = section.find(class_='sectionname')
        section_title = section_name.text.strip() if section_name else "Unbenannte Sektion"
        
        # Finde alle Aktivitäten in dieser Sektion
        activities = section.select('li.activity')
        for activity in activities:
            activity_link = activity.find('a')
            if activity_link:
                activity_name = activity_link.text.strip()
                activity_url = activity_link.get('href')
                
                # Prüfe, ob es sich um einen Kurs handelt
                if 'course/view.php' in activity_url or 'mod/resource' in activity_url:
                    courses.append({
                        'name': f"{semester_name} - {section_title} - {activity_name}",
                        'url': activity_url
                    })
    
    # Falls keine Sektionen gefunden wurden, versuche alle Kurslinks zu finden
    if not courses:
        courses = find_all_available_courses(soup)
        # Füge Semestername zu jedem Kurs hinzu
        for course in courses:
            course['name'] = f"{semester_name} - {course['name']}"
    
    return courses

def test_connection(url, username, password):
    """Teste die Verbindung zu Moodle ohne vollständigen Scrape."""
    try:
        session = login_to_moodle(url, username, password)
        if session:
            return True, "Verbindung erfolgreich hergestellt!"
        else:
            return False, "Anmeldung fehlgeschlagen. Überprüfe deine Zugangsdaten."
    except Exception as e:
        return False, f"Fehler beim Verbindungsaufbau: {str(e)}"

def run_sync(url, username, password):
    """Führe eine vollständige Synchronisierung mit Moodle durch."""
    try:
        ensure_dirs_exist()
        
        print(f"Moodle-Scraper startet für URL: {url}")
        print(f"Benutzer: {username}")
        
        session = login_to_moodle(url, username, password)
        if not session:
            return False, "Anmeldung fehlgeschlagen", 0, 0, 0
        
        print("\nNavigation durch Moodle-Struktur...")
        courses = get_courses(session, url)
        
        # Für jeden Kurs nach Bewertungen/Aufgaben suchen
        courses_with_assignments = []
        overdue_assignments = []
        total_assignments = 0
        
        for course in courses:
            assignment_details = get_assignment_details(session, course)
            course['assignments'] = assignment_details.get('assignments', [])
            course['has_assignments'] = assignment_details.get('has_assignments', False)
            
            if course['has_assignments']:
                courses_with_assignments.append(course)
                total_assignments += len(course['assignments'])
                
                # Sammle überfällige Aufgaben
                for assignment in course['assignments']:
                    if assignment.get('is_overdue'):
                        overdue_assignments.append({
                            'course_name': course['name'],
                            'assignment_name': assignment['name'],
                            'due_date': assignment.get('due_date', 'Unbekannt'),
                            'remaining_time': assignment.get('remaining_time', 'Unbekannt'),
                            'url': assignment.get('url', '')
                        })
        
        # Speichere die gefundenen Kurse und Aufgaben in CSV-Dateien
        kurse_csv_path = os.path.join(OUTPUT_DIR, "alle_kurse.csv")
        assignments_csv_path = os.path.join(OUTPUT_DIR, "alle_aufgaben.csv")
        overdue_csv_path = os.path.join(OUTPUT_DIR, "ueberfaellige_aufgaben.csv")
        
        # Speichere Kurse
        with open(kurse_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'url', 'has_assignments']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for course in courses:
                writer.writerow({
                    'name': course['name'],
                    'url': course['url'],
                    'has_assignments': course['has_assignments']
                })
        
        # Speichere alle Aufgaben
        if any(course['has_assignments'] for course in courses):
            with open(assignments_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['course_name', 'assignment_name', 'opening_date', 'due_date', 'remaining_time', 'is_overdue', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for course in courses:
                    if course['has_assignments']:
                        for assignment in course['assignments']:
                            writer.writerow({
                                'course_name': course['name'],
                                'assignment_name': assignment['name'],
                                'opening_date': assignment.get('opening_date', ''),
                                'due_date': assignment.get('due_date', ''),
                                'remaining_time': assignment.get('remaining_time', ''),
                                'is_overdue': assignment.get('is_overdue', False),
                                'url': assignment.get('url', '')
                            })
        
        # Speichere überfällige Aufgaben
        if overdue_assignments:
            with open(overdue_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['course_name', 'assignment_name', 'due_date', 'remaining_time', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for assignment in overdue_assignments:
                    writer.writerow(assignment)
        
        # Ausgabe der Ergebnisse in JSON-Format für die UI
        results = {
            'courses': len(courses),
            'courses_with_assignments': len(courses_with_assignments),
            'assignments': total_assignments,
            'overdue_assignments': len(overdue_assignments)
        }
        
        print(f"\nErgebnisse: {results}")
        return True, "Synchronisierung erfolgreich!", len(courses), total_assignments, len(overdue_assignments)
    
    except Exception as e:
        print(f"Fehler bei der Synchronisierung: {str(e)}")
        traceback.print_exc()
        return False, f"Fehler: {str(e)}", 0, 0, 0

def create_command_interface():
    """Erstellt eine Kommandozeilenschnittstelle für den Moodle-Scraper."""
    parser = argparse.ArgumentParser(description='Moodle-Kurs und Aufgaben Scraper')
    subparsers = parser.add_subparsers(dest='command', help='Befehle')
    
    # Test-Verbindung Befehl
    test_parser = subparsers.add_parser('test', help='Testet die Verbindung zu Moodle')
    
    # Sync Befehl
    sync_parser = subparsers.add_parser('sync', help='Synchronisiert Kurse und Aufgaben von Moodle')
    
    # Argumente für beide Befehle
    for p in [test_parser, sync_parser]:
        p.add_argument('--url', help='Moodle-URL')
        p.add_argument('--username', help='Benutzername')
        p.add_argument('--password', help='Passwort')
        p.add_argument('--config', action='store_true', help='Zugangsdaten aus Konfigurationsdatei laden')
    
    return parser

def main():
    """Hauptfunktion für die Kommandozeilenschnittstelle."""
    parser = create_command_interface()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Lade Konfiguration, wenn gewünscht oder wenn keine Zugangsdaten angegeben wurden
    config = None
    if args.config or (not args.url and not args.username and not args.password):
        config = load_config()
    
    # Bestimme Zugangsdaten (Kommandozeile hat Vorrang vor Konfigurationsdatei)
    url = args.url or (config and config.get('moodle_url'))
    username = args.username or (config and config.get('username'))
    password = args.password or (config and config.get('password'))
    
    if not url or not username or not password:
        print("Fehler: Moodle-URL, Benutzername und Passwort müssen angegeben werden.")
        return
    
    # Führe den entsprechenden Befehl aus
    if args.command == 'test':
        success, message = test_connection(url, username, password)
        print(message)
        sys.exit(0 if success else 1)
    
    elif args.command == 'sync':
        success, message, course_count, assignment_count, overdue_count = run_sync(url, username, password)
        if success:
            # Aktualisiere die Konfigurationsdatei mit den Ergebnissen
            update_sync_results(course_count, assignment_count, overdue_count)
            
            print(f"Synchronisierung erfolgreich!")
            print(f"Gefundene Kurse: {course_count}")
            print(f"Gefundene Aufgaben: {assignment_count}")
            print(f"Überfällige Aufgaben: {overdue_count}")
            sys.exit(0)
        else:
            print(f"Synchronisierung fehlgeschlagen: {message}")
            sys.exit(1)

if __name__ == "__main__":
    main()