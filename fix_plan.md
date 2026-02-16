# Fix Plan – ZeitTracker Improvements

## Session 5 – All 8 Issues Fixed ✅

---

### 1. Abteilungsleiter: Benutzer der eigenen Abteilung verwalten
- **Problem**: Abteilungsleiter kann keine Benutzer seiner Abteilung einsehen/verwalten.
- **Fix**: 
  - Backend: `GET /api/v1/users` für Abteilungsleiter freigeben (nur eigene Abteilung)
  - Backend: `PUT /api/v1/users/{id}` für Abteilungsleiter erlauben (nur eigene Abteilung, kein Rollenwechsel)
  - Frontend: Admin-Tab auch für Abteilungsleiter sichtbar machen (eingeschränkt)

### 2. Admin: Benutzerübersicht sortiert nach Abteilung
- **Problem**: Benutzerliste ist unsortiert, kein Überblick nach Abteilungen.
- **Fix**:
  - Backend: Users-Endpoint um Department-Info erweitern (JOIN)
  - Frontend: Benutzer nach Abteilung gruppiert anzeigen mit Überschriften

### 3. Abteilungen umbenennen und löschen
- **Problem**: Keine Möglichkeit, Abteilungen umzubenennen oder zu löschen.
- **Fix**:
  - Backend: `PUT /api/v1/departments/{id}` zum Umbenennen
  - Backend: `DELETE /api/v1/departments/{id}` nur wenn 0 Mitglieder
  - Frontend: Edit/Delete Buttons im Department-Management

### 4. Feiertage automatisch erkennen (Deutschland)
- **Problem**: Feiertage müssen manuell eingetragen werden.
- **Fix**:
  - Backend: Deutsche Feiertage automatisch berechnen (Ostern-basiert + feste)
  - Backend: `POST /api/v1/holidays/auto-generate?year=2026&state=all` Endpoint
  - Frontend: Button "Feiertage automatisch laden" im Admin-Panel

### 5. Soll-Arbeitszeit einstellen
- **Problem**: Keine UI zum Einstellen der Soll-Arbeitszeit pro Benutzer.
- **Fix**:
  - Frontend: Schedule-Bereich im Admin-Panel (pro User Wochentage Mo-Fr Stunden)
  - Backend: Schedule-Router ist vorhanden, wird nur nicht im UI genutzt

### 6. Überstunden-Schutz & Export-Markierung
- **Problem**: Überstunden können auch bei negativem Saldo genommen werden. Keine Markierung im Export.
- **Fix**:
  - Backend: Prüfung im `use-overtime` Endpoint: Balance >= angeforderte Minuten
  - Backend: Export-Service: Überstunden-Spalte/Markierung in PDF/Excel/CSV
  - Frontend: Button deaktivieren wenn Balance ≤ 0

### 7. Urlaubstage verwalten (Admin/Abteilungsleiter)
- **Problem**: Keine Möglichkeit, Urlaubskontingent pro Benutzer einzustellen.
- **Fix**:
  - Backend: `PUT /api/v1/absences/budget/{user_id}` Endpoint
  - Frontend: Urlaubstage-Feld in der Benutzerverwaltung

### 8. Überstunden in Berichte-Übersicht anzeigen
- **Problem**: Überstundensaldo wird im Reports-Tab nicht dargestellt.
- **Fix**:
  - Frontend: Überstunden-Zusammenfassung im Bericht-Header (Saldo, Monatsdelta)
  - Daten kommen bereits vom `/reports/monthly` Endpoint

### 9. Kalender: Nur Einträge des gewählten Datums anzeigen
- **Problem**: Calendar zeigt immer alle Einträge statt nur die des ausgewählten Tages.
- **Fix**:
  - Frontend: `calendar.js` → Einträge nach `selectedDate` filtern
  - Nur Einträge anzeigen deren Datum mit dem geklickten Tag übereinstimmt

### 10. Auto-Logout mit Session-Timer
- **Problem**: Kein Auto-Logout, Session läuft still ab.
- **Fix**:
  - Frontend: Session-Timer oben rechts in der Ecke (Countdown bis Token-Ablauf)
  - Auto-Refresh bei Aktivität, Auto-Logout bei Inaktivität (15 Min)
  - Warnung 2 Minuten vor Ablauf

---

## Priorität
1. Kalender-Fix (Bug) ← kritisch
2. Soll-Zeit + Überstunden-Logik ← Kernfunktion
3. Überstunden in Berichten + Export
4. Auto-Logout
5. Abteilungsleiter-Rechte
6. Feiertage auto-detect
7. Abteilungen umbenennen/löschen
8. Urlaubstage-Verwaltung
9. Admin-Übersicht sortiert
