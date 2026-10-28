*** Settings ***
Documentation    Render reads using an existing USER. No mutations, payments, cross-account probes or local synthetic IDs. Explicit remote runner only.
Library    ../resources/remote_api.py
Suite Setup    Open Remote Session
Suite Teardown    Close Remote Session
Test Template    Check Remote
Test Tags    remote    readonly

*** Test Cases ***
REM-001 Health                       health
REM-002 Public Bus                   bus
REM-003 Public Lines                 lines
REM-004 Public Tickets               tickets
REM-005 Anonymous Subscription Types    anonymous-types
REM-006 Own Profile                  profile
REM-007 Own Dossier                  dossier
REM-008 Own Subscription             subscription
REM-009 Own History                  history
REM-010 Own Cards                    cards
REM-011 Own Activities               activities
REM-012 Authenticated Types          authenticated-types
