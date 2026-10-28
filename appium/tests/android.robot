*** Settings ***
Documentation    Android journeys against a recorded APK for local QA or explicitly selected Render. No registration submission, login request, email, payment or deletion.
Resource    ../resources/mobile.resource
Test Setup    Start From Login
Test Teardown    Finish Mobile Test
Test Tags    android    appium    non-destructive

*** Test Cases ***
MOB-001 Login Screen
    [Tags]    smoke
    Mobile Text Should Be Visible    Connexion
    Mobile Text Should Be Visible    Se Connecter

MOB-002 Login Password Is Masked
    Mobile Password Should Be Masked

MOB-003 Email Input Accepts Text
    Enter Mobile Field    0    qa-mobile@example.invalid
    Mobile Field Should Equal    0    qa-mobile@example.invalid

MOB-004 Registration Navigation
    Open Registration
    Mobile Text Should Be Visible    Prénom*

MOB-005 Empty Names Are Rejected
    Open Registration
    Tap Mobile Text    Suivant
    Mobile Text Should Be Visible    Nom obligatoire
    Mobile Text Should Be Visible    Prénom obligatoire

MOB-006 Missing First Name Is Rejected
    Open Registration
    Enter Mobile Field    0    Synthetic
    Tap Mobile Text    Suivant
    Mobile Text Should Be Visible    Prénom obligatoire

MOB-007 Missing Last Name Is Rejected
    Open Registration
    Enter Mobile Field    1    QA
    Tap Mobile Text    Suivant
    Mobile Text Should Be Visible    Nom obligatoire

MOB-008 Valid Names Advance Registration
    Fill Registration Names
    Tap Mobile Text    Suivant
    Mobile Text Should Be Visible    Adresse*
    Mobile Text Should Be Visible    Précédent

MOB-009 Previous Step Preserves Names
    Fill Registration Names
    Tap Mobile Text    Suivant
    Tap Mobile Text    Précédent
    Mobile Field Should Equal    0    Synthetic
    Mobile Field Should Equal    1    QA

MOB-010 Registration Returns To Login
    Open Registration
    Tap Mobile Text    Se connecter
    Mobile Text Should Be Visible    Bienvenue sur eBus

MOB-011 Recovery Navigation
    Open Recovery
    Mobile Text Should Be Visible    Retour à la connexion

MOB-012 Recovery Returns To Login
    Open Recovery
    Tap Mobile Text    Retour à la connexion
    Mobile Text Should Be Visible    Bienvenue sur eBus

MOB-013 Android Back From Recovery
    Open Recovery
    Mobile Back
    Mobile Text Should Be Visible    Bienvenue sur eBus

MOB-014 Administrator Login Navigation
    Tap Mobile Text    Accès administrateur
    Mobile Text Should Be Visible    Connexion Admin
    Mobile Password Should Be Masked

MOB-015 Android Back From Registration
    Open Registration
    Mobile Back
    Mobile Text Should Be Visible    Bienvenue sur eBus

MOB-016 Guest Home
    Open Guest Home
    Mobile Text Should Be Visible    Objets perdus
    Mobile Text Should Be Visible    Réclamations

MOB-017 Guest Lines
    Open Guest Home
    Tap Mobile Text    Lignes
    Mobile Text Should Be Visible    Lignes de bus
    Mobile Lines Should Match Api

MOB-018 Guest Claims
    Open Guest Home
    Tap Mobile Text    Réclamations
    Mobile Text Should Be Visible    Réclamations

MOB-019 Guest Payment Requires Login
    Open Guest Home
    Tap Mobile Text    Paiement
    Mobile Text Should Be Visible    Connexion requise

MOB-020 Guest Cancels Login Dialog
    Open Guest Home
    Tap Mobile Text    Paiement
    Mobile Text Should Be Visible    Connexion requise
    Tap Mobile Text    Annuler
    Mobile Text Should Be Visible    Lignes
