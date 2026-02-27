*** Settings ***
Library    SSHLibrary
Library    Collections
Variables  ../inventory.yaml

*** Keywords ***

Connect To Device
    [Arguments]    ${device_type}    ${device_name}

    Log    Connecting to ${device_type} -> ${device_name}

    Dictionary Should Contain Key    ${devices}    ${device_type}
    ${device_group}=    Get From Dictionary    ${devices}    ${device_type}

    Dictionary Should Contain Key    ${device_group}    ${device_name}
    ${device}=    Get From Dictionary    ${device_group}    ${device_name}

    ${host}=        Get From Dictionary    ${device}    host
    ${username}=    Get From Dictionary    ${device}    username
    ${password}=    Get From Dictionary    ${device}    password
    ${port}=        Get From Dictionary    ${device}    port
    ${protocol}=    Get From Dictionary    ${device}    protocol

    Run Keyword If    '${protocol}' == 'ssh'    Connect Via SSH
    ...    ${host}    ${port}    ${username}    ${password}
    ...    ELSE    Fail    Unsupported protocol: ${protocol}


Connect Via SSH
    [Arguments]    ${host}    ${port}    ${username}    ${password}

    Open Connection    ${host}    port=${port}    timeout=30s
    Login    ${username}    ${password}


Disconnect Device
    Close Connection
