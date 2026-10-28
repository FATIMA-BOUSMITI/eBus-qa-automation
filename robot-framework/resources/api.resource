*** Settings ***
Library    api_library.py

*** Keywords ***
Public Array Is Available
    [Arguments]    ${path}
    Connect To Local Api
    Request Api    GET    ${path}
    Response Status Should Be    200
    Response Should Be Array

Access Must Be Denied
    [Arguments]    ${path}
    Connect To Local Api    user
    Request Api    GET    ${path}
    Response Status Should Be    403

Invalid Credentials Are Rejected
    [Arguments]    ${payload}
    Connect To Local Api
    Request Api    POST    /users/login    ${payload}
    Response Status Should Be    400    401
