*** Settings ***
Library    SSHLibrary
Library    Collections
Variables  ../inventory.yaml


*** Keywords ***

Connect To Device
    [Arguments]    ${device_type}    ${device_name}

    # Validate device type
    Dictionary Should Contain Key    ${devices}    ${device_type}
    ${device_group}=    Get From Dictionary    ${devices}    ${device_type}

    # Validate device name
    Dictionary Should Contain Key    ${device_group}    ${device_name}
    ${device}=    Get From Dictionary    ${device_group}    ${device_name}

    ${host}=        Get From Dictionary    ${device}    host
    ${username}=    Get From Dictionary    ${device}    username
    ${password}=    Get From Dictionary    ${device}    password
    ${port}=        Get From Dictionary    ${device}    port
    ${protocol}=    Get From Dictionary    ${device}    protocol

    Log    Connecting to ${device_type} -> ${device_name} (${host})

    Run Keyword If    '${protocol}' == 'ssh'    Connect Via SSH
    ...    ${host}    ${port}    ${username}    ${password}    ${device_name}
    ...    ELSE IF    '${protocol}' == 'telnet'    Connect Via Telnet
    ...    ${host}    ${port}    ${username}    ${password}    ${device_name}
    ...    ELSE    Fail    Unsupported protocol: ${protocol}


Connect Via SSH
    [Arguments]    ${host}    ${port}    ${username}    ${password}    ${alias}
    Open Connection    ${host}    port=${port}    timeout=30s    alias=${alias}
    Login    ${username}    ${password}


Connect Via Telnet
    [Arguments]    ${host}    ${port}    ${username}    ${password}    ${alias}
    Open Connection    ${host}    port=${port}    timeout=30s    alias=${alias}
    Login    ${username}    ${password}


Disconnect Device
    [Arguments]    ${device_name}
    Switch Connection    ${device_name}
    Close Connection
