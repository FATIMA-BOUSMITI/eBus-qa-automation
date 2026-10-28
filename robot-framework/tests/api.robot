*** Settings ***
Documentation    Source-verified local API regression. Requires qa/seed.sql fixtures; tests never call Render. No data created; no cleanup beyond session closure.
Resource    ../resources/api.resource
Test Teardown    Close Api Session

*** Test Cases ***
ROB-001 Health
    [Tags]    smoke
    Connect To Local Api
    Request Api    GET    /api/health
    Response Status Should Be    200
    Response Text Should Be    UP

ROB-002 Public Bus Catalogue
    [Template]    Public Array Is Available
    /bus

ROB-003 Public Line Catalogue
    [Template]    Public Array Is Available
    /lignes

ROB-004 Public Tickets
    [Template]    Public Array Is Available
    /tickets

ROB-005 Anonymous Subscription Types
    [Template]    Public Array Is Available
    /types-abonnement

ROB-006 Own Profile
    Connect To Local Api    user
    Request Api    GET    /users/2
    Response Status Should Be    200
    Response Field Should Be    id    2

ROB-007 Own Dossier
    Connect To Local Api    user
    Request Api    GET    /users/me/dossier?id=2
    Response Status Should Be    200
    Response Field Should Be    statusDossier    VALIDE

ROB-008 Own Subscription
    Connect To Local Api    user
    Request Api    GET    /abonnements/user/2
    Response Status Should Be    200
    Response Field Should Be    userId    2
    Response Field Should Be    status    EXPIRE

ROB-009 Own History
    Connect To Local Api    user
    Request Api    GET    /abonnements/user/2/historique
    Response Status Should Be    200
    Response Should Be Array

ROB-010 Admin Dossiers
    Connect To Local Api    admin
    Request Api    GET    /admin/dossiers
    Response Status Should Be    200
    Response Should Be Array

ROB-011 Other Profile Denied
    [Template]    Access Must Be Denied
    /users/3

ROB-012 Test Controller Bypass Denied
    [Template]    Access Must Be Denied
    /test/user/3

ROB-013 Other Subscription Denied
    [Template]    Access Must Be Denied
    /abonnements/user/3

ROB-014 Other Cards Denied
    [Template]    Access Must Be Denied
    /cards/user/3

ROB-015 Admin User List Denied
    [Template]    Access Must Be Denied
    /users

ROB-016 Invalid Login Data Driven
    [Template]    Invalid Credentials Are Rejected
    {"email":"qa-nonexistent@example.invalid","password":"Invalid-Only-4927"}
    {"email":"qa-user@example.invalid","password":"Known-Wrong-Only-4927"}
    {"email":"","password":""}

ROB-017 Pending Dossier Refused
    Connect To Local Api    pending
    Request Api    POST    /abonnements/subscribe?userId=4&typeId=1
    Response Status Should Be    400

ROB-018 Rejected Dossier Refused
    Connect To Local Api    rejected
    Request Api    POST    /abonnements/subscribe?userId=5&typeId=1
    Response Status Should Be    400

ROB-019 Inactive Offer Refused
    Connect To Local Api    user
    Request Api    POST    /abonnements/subscribe?userId=2&typeId=2
    Response Status Should Be    400

ROB-020 Recovery Of Missing Object Denied To User
    Connect To Local Api    user
    Request Api    POST    /api/objets/9223372036854775806/signaler-recupere
    Response Status Should Be    403
