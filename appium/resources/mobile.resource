*** Settings ***
Library    mobile.py

*** Keywords ***
Start From Login
    Open Mobile

Finish Mobile Test
    Mobile Failure Evidence
    Close Mobile

Open Registration
    Tap Mobile Text    S'inscrire
    Mobile Text Should Be Visible    Nom*

Fill Registration Names
    Open Registration
    Enter Mobile Field    0    Synthetic
    Enter Mobile Field    1    QA

Open Guest Home
    Tap Mobile Text    Continuer en tant qu'invité
    Mobile Text Should Be Visible    Lignes

Open Recovery
    Tap Mobile Text    Mot de passe oublié ?
    Mobile Text Should Be Visible    Envoyer le code
