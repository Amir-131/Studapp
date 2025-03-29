/**
 * moodle-connector.js
 * Diese Datei implementiert die Kommunikation zwischen der Weboberfläche
 * und dem Python-Skript für die Moodle-Integration.
 */

const MoodleConnector = {
    /**
     * Testet die Verbindung zu Moodle mit den angegebenen Zugangsdaten
     * @param {string} url - Moodle-URL
     * @param {string} username - Benutzername
     * @param {string} password - Passwort
     * @returns {Promise} - Erfolgsmeldung oder Fehlermeldung
     */
    testConnection: async function(url, username, password) {
        try {
            // Erzeuge einen Befehlsstring für die Python-Skript-Ausführung
            const command = `python3 scraper.py test --url "${url}" --username "${username}" --password "${password}"`;
            
            // In einer realen Anwendung würde hier ein Aufruf zum Backend erfolgen
            // Für Demonstrationszwecke simulieren wir den Prozess
            console.log(`Führe Befehl aus: ${command}`);
            
            // Simulierte Verzögerung, um API-Aufruf nachzuahmen
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Für Demo-Zwecke: Zufälliges Ergebnis mit 80% Erfolgswahrscheinlichkeit
            const isSuccessful = Math.random() > 0.2;
            
            if (isSuccessful) {
                return {
                    success: true,
                    message: "Verbindung erfolgreich hergestellt!"
                };
            } else {
                return {
                    success: false,
                    message: "Verbindung fehlgeschlagen. Bitte überprüfe deine Zugangsdaten."
                };
            }
        } catch (error) {
            console.error("Fehler beim Testen der Verbindung:", error);
            return {
                success: false,
                message: `Fehler: ${error.message}`
            };
        }
    },
    
    /**
     * Führt eine vollständige Synchronisierung mit Moodle durch
     * @param {string} url - Moodle-URL
     * @param {string} username - Benutzername
     * @param {string} password - Passwort
     * @returns {Promise} - Ergebnis der Synchronisierung
     */
    syncData: async function(url, username, password) {
        try {
            // Erzeuge einen Befehlsstring für die Python-Skript-Ausführung
            const command = `python3 scraper.py sync --url "${url}" --username "${username}" --password "${password}"`;
            
            // In einer realen Anwendung würde hier ein Aufruf zum Backend erfolgen
            console.log(`Führe Befehl aus: ${command}`);
            
            // Simulierte Verzögerung, um API-Aufruf nachzuahmen
            await new Promise(resolve => setTimeout(resolve, 2500));
            
            // Für Demo-Zwecke: Zufälliges Ergebnis mit 80% Erfolgswahrscheinlichkeit
            const isSuccessful = Math.random() > 0.2;
            
            if (isSuccessful) {
                // Simuliere Ergebnisse für die Demo
                const courseCount = Math.floor(Math.random() * 10) + 5;
                const assignmentCount = Math.floor(Math.random() * 20) + 10;
                const overdueCount = Math.floor(Math.random() * 5);
                
                return {
                    success: true,
                    message: "Synchronisierung erfolgreich abgeschlossen!",
                    data: {
                        courseCount,
                        assignmentCount,
                        overdueCount,
                        lastSync: new Date().toLocaleString()
                    }
                };
            } else {
                return {
                    success: false,
                    message: "Synchronisierung fehlgeschlagen. Bitte versuche es später erneut."
                };
            }
        } catch (error) {
            console.error("Fehler bei der Synchronisierung:", error);
            return {
                success: false,
                message: `Fehler: ${error.message}`
            };
        }
    },
    
    /**
     * Speichert die Moodle-Zugangsdaten und konfiguriert die automatische Synchronisierung
     * @param {string} url - Moodle-URL
     * @param {string} username - Benutzername
     * @param {string} password - Passwort
     * @param {boolean} autoSync - Automatische Synchronisierung aktivieren/deaktivieren
     * @returns {Promise} - Ergebnis des Speichervorgangs
     */
    saveCredentials: async function(url, username, password, autoSync) {
        try {
            // Speichere die Credentials sicher im localStorage
            // In einer echten Anwendung sollte das Passwort NIEMALS unverschlüsselt gespeichert werden!
            localStorage.setItem('moodleUrl', url);
            localStorage.setItem('moodleUsername', username);
            localStorage.setItem('moodlePassword', password); // In der Praxis: verschlüsseln!
            localStorage.setItem('moodleAutoSync', autoSync);
            
            console.log("Moodle-Zugangsdaten gespeichert");
            
            // In einer realen Anwendung würden wir die Konfiguration auch in eine Datei schreiben,
            // die das Python-Skript lesen kann
            const configData = {
                moodle_url: url,
                username: username,
                password: password,
                auto_sync: autoSync
            };
            
            console.log("Konfigurationsdaten für Python-Skript:", configData);
            
            // Simulierte Verzögerung, um API-Aufruf nachzuahmen
            await new Promise(resolve => setTimeout(resolve, 500));
            
            return {
                success: true,
                message: "Moodle-Zugangsdaten wurden gespeichert."
            };
        } catch (error) {
            console.error("Fehler beim Speichern der Zugangsdaten:", error);
            return {
                success: false,
                message: `Fehler: ${error.message}`
            };
        }
    },
    
    /**
     * Lädt die gespeicherten Moodle-Zugangsdaten
     * @returns {Object} - Die gespeicherten Zugangsdaten oder null
     */
    loadCredentials: function() {
        try {
            const url = localStorage.getItem('moodleUrl');
            const username = localStorage.getItem('moodleUsername');
            const password = localStorage.getItem('moodlePassword');
            const autoSync = localStorage.getItem('moodleAutoSync') === 'true';
            
            if (url && username && password) {
                return {
                    url,
                    username,
                    password,
                    autoSync
                };
            }
            
            return null;
        } catch (error) {
            console.error("Fehler beim Laden der Zugangsdaten:", error);
            return null;
        }
    },
    
    /**
     * Lädt die Ergebnisse der letzten Synchronisierung
     * @returns {Object} - Die Ergebnisse der letzten Synchronisierung oder null
     */
    loadLastSyncResults: function() {
        try {
            const lastSync = localStorage.getItem('moodleLastSync');
            if (!lastSync) return null;
            
            return {
                lastSync,
                courseCount: localStorage.getItem('moodleCourseCount') || '0',
                assignmentCount: localStorage.getItem('moodleAssignmentCount') || '0',
                overdueCount: localStorage.getItem('moodleOverdueCount') || '0'
            };
        } catch (error) {
            console.error("Fehler beim Laden der letzten Synchronisierungsergebnisse:", error);
            return null;
        }
    },
    
    /**
     * Installiert das Cronjob-Setup für automatische Synchronisierung
     * @param {boolean} enabled - Aktivieren oder deaktivieren
     * @returns {Promise} - Ergebnis der Operation
     */
    setupAutoSync: async function(enabled) {
        try {
            // In einer realen Anwendung würden wir einen Cronjob oder
            // eine andere Methode zur regelmäßigen Ausführung einrichten
            console.log(`Automatische Synchronisierung ${enabled ? 'aktiviert' : 'deaktiviert'}`);
            
            // Simulierte Verzögerung, um API-Aufruf nachzuahmen
            await new Promise(resolve => setTimeout(resolve, 500));
            
            return {
                success: true,
                message: `Automatische Synchronisierung wurde ${enabled ? 'aktiviert' : 'deaktiviert'}.`
            };
        } catch (error) {
            console.error("Fehler beim Einrichten der automatischen Synchronisierung:", error);
            return {
                success: false,
                message: `Fehler: ${error.message}`
            };
        }
    }
};

// Füge einen Event-Listener hinzu, der die Moodle-Integration aktiviert,
// sobald die Seite geladen ist
document.addEventListener('DOMContentLoaded', function() {
    // Integration des MoodleConnectors in die Einstellungsseite
    const moodleForm = document.getElementById('moodleForm');
    const testConnectionBtn = document.getElementById('testConnectionBtn');
    const syncNowBtn = document.getElementById('syncNowBtn');
    
    if (moodleForm) {
        // Lade gespeicherte Zugangsdaten
        const credentials = MoodleConnector.loadCredentials();
        if (credentials) {
            document.getElementById('moodleUrl').value = credentials.url;
            document.getElementById('moodleUsername').value = credentials.username;
            document.getElementById('moodlePassword').value = credentials.password;
            document.getElementById('autoSyncCheckbox').checked = credentials.autoSync;
            
            // Update status dot
            const statusDot = document.getElementById('moodleStatusDot');
            const statusText = document.getElementById('moodleStatusText');
            if (statusDot && statusText) {
                statusDot.classList.remove('inactive');
                statusDot.classList.add('success');
                statusText.textContent = 'Verbunden';
            }
        }
        
        // Lade letzte Synchronisierungsergebnisse
        const lastSyncResults = MoodleConnector.loadLastSyncResults();
        if (lastSyncResults) {
            document.getElementById('lastSyncTime').textContent = `Letzte Synchronisierung: ${lastSyncResults.lastSync}`;
            
            const syncStats = document.getElementById('syncStats');
            if (syncStats) {
                syncStats.children[0].querySelector('.text-xl').textContent = lastSyncResults.courseCount;
                syncStats.children[1].querySelector('.text-xl').textContent = lastSyncResults.assignmentCount;
                syncStats.children[2].querySelector('.text-xl').textContent = lastSyncResults.overdueCount;
            }
        }
        
        // Event-Handler für Formular
        moodleForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const url = document.getElementById('moodleUrl').value;
            const username = document.getElementById('moodleUsername').value;
            const password = document.getElementById('moodlePassword').value;
            const autoSync = document.getElementById('autoSyncCheckbox').checked;
            
            if (!url || !username || !password) {
                showMoodleStatus('error', 'Bitte fülle alle Felder aus.');
                return;
            }
            
            // Speichere Zugangsdaten
            const saveResult = await MoodleConnector.saveCredentials(url, username, password, autoSync);
            
            if (saveResult.success) {
                updateMoodleStatus('success');
                showMoodleStatus('success', saveResult.message);
                
                // Richte automatische Synchronisierung ein, wenn aktiviert
                if (autoSync) {
                    await MoodleConnector.setupAutoSync(true);
                }
                
                // Führe die Synchronisierung sofort durch, wenn gespeichert wurde
                syncMoodleData();
            } else {
                updateMoodleStatus('error');
                showMoodleStatus('error', saveResult.message);
            }
        });
        
        // Event-Handler für Test-Verbindung
        if (testConnectionBtn) {
            testConnectionBtn.addEventListener('click', async function() {
                const url = document.getElementById('moodleUrl').value;
                const username = document.getElementById('moodleUsername').value;
                const password = document.getElementById('moodlePassword').value;
                
                if (!url || !username || !password) {
                    showMoodleStatus('error', 'Bitte fülle alle Felder aus.');
                    return;
                }
                
                showMoodleStatus('pending', 'Verbindung wird getestet...');
                
                const result = await MoodleConnector.testConnection(url, username, password);
                
                if (result.success) {
                    updateMoodleStatus('success');
                    showMoodleStatus('success', result.message);
                } else {
                    updateMoodleStatus('error');
                    showMoodleStatus('error', result.message);
                }
            });
        }
        
        // Event-Handler für Jetzt-Synchronisieren
        if (syncNowBtn) {
            syncNowBtn.addEventListener('click', function() {
                syncMoodleData();
            });
        }
    }
});

// Helper-Funktionen für die Moodle-Integrationsseite
function showMoodleStatus(type, message) {
    const statusElement = document.getElementById('moodleStatus');
    if (!statusElement) return;
    
    statusElement.innerHTML = '';
    statusElement.classList.remove('success', 'error');
    
    if (type === 'pending') {
        const spinner = document.createElement('span');
        spinner.className = 'spinner';
        
        const messageSpan = document.createElement('span');
        messageSpan.textContent = message;
        
        statusElement.classList.add('success');
        statusElement.appendChild(spinner);
        statusElement.appendChild(messageSpan);
    } else {
        statusElement.classList.add(type);
        statusElement.textContent = message;
    }
    
    statusElement.style.display = 'block';
}

function updateMoodleStatus(status) {
    const statusDot = document.getElementById('moodleStatusDot');
    const statusText = document.getElementById('moodleStatusText');
    
    if (!statusDot || !statusText) return;
    
    statusDot.classList.remove('success', 'error', 'warning', 'inactive');
    
    switch (status) {
        case 'success':
            statusDot.classList.add('success');
            statusText.textContent = 'Verbunden';
            break;
        case 'error':
            statusDot.classList.add('error');
            statusText.textContent = 'Fehler bei der Verbindung';
            break;
        case 'warning':
            statusDot.classList.add('warning');
            statusText.textContent = 'Verbindungsprobleme';
            break;
        default:
            statusDot.classList.add('inactive');
            statusText.textContent = 'Nicht verbunden';
    }
}

async function syncMoodleData() {
    const credentials = MoodleConnector.loadCredentials();
    if (!credentials) {
        showMoodleStatus('error', 'Keine Zugangsdaten gespeichert. Bitte speichere deine Zugangsdaten zuerst.');
        return;
    }
    
    showMoodleStatus('pending', 'Synchronisierung läuft...');
    
    const result = await MoodleConnector.syncData(
        credentials.url,
        credentials.username,
        credentials.password
    );
    
    if (result.success) {
        // Speichere die Ergebnisse
        localStorage.setItem('moodleLastSync', result.data.lastSync);
        localStorage.setItem('moodleCourseCount', result.data.courseCount);
        localStorage.setItem('moodleAssignmentCount', result.data.assignmentCount);
        localStorage.setItem('moodleOverdueCount', result.data.overdueCount);
        
        // Aktualisiere die Anzeige
        document.getElementById('lastSyncTime').textContent = `Letzte Synchronisierung: ${result.data.lastSync}`;
        
        const syncStats = document.getElementById('syncStats');
        if (syncStats) {
            syncStats.children[0].querySelector('.text-xl').textContent = result.data.courseCount;
            syncStats.children[1].querySelector('.text-xl').textContent = result.data.assignmentCount;
            syncStats.children[2].querySelector('.text-xl').textContent = result.data.overdueCount;
        }
        
        updateMoodleStatus('success');
        showMoodleStatus('success', `Synchronisierung erfolgreich! ${result.data.courseCount} Kurse, ${result.data.assignmentCount} Aufgaben und ${result.data.overdueCount} überfällige Abgaben gefunden.`);
    } else {
        updateMoodleStatus('error');
        showMoodleStatus('error', result.message);
    }
}