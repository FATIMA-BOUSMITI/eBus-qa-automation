*** Settings ***
Documentation    Real UI -> remote authentication -> account profile -> logout. Existing accounts only; no entity creation, modification, payment or deletion. Credential aliases never contain secrets.
Resource    ../resources/mobile.resource
Test Setup    Start From Login
Test Teardown    Finish Mobile Test
Test Tags    android    appium    authenticated-e2e    non-destructive
Test Template    Existing Account Completes Session

*** Test Cases ***
E2E-AUTH-001 First Existing Account     ACCOUNT1
E2E-AUTH-002 Second Existing Account    ACCOUNT2
E2E-AUTH-003 Third Existing Account     ACCOUNT3

*** Keywords ***
Existing Account Completes Session
    [Arguments]    ${account}
    Login Existing Mobile Account    ${account}
    Mobile Profile Should Match Account
    Logout Mobile Account
