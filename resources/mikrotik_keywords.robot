*** Settings ***
Library    SSHLibrary
Library    Collections
Library    String


*** Keywords ***

Get All Ethernet Ports
    ${output}=    Execute Command    /interface ethernet print terse
    @{lines}=    Split To Lines    ${output}
    ${ports}=    Create List

    FOR    ${line}    IN    @{lines}
        ${trimmed}=    Strip String    ${line}
        Run Keyword If    '${trimmed}' == ''    Continue For Loop
        ${port}=    Fetch From Left    ${trimmed}    " "
        Append To List    ${ports}    ${port}
    END

    Return    ${ports}


Get SSH Management Port
    # Extract the active SSH interface
    ${conn_info}=    Execute Command    /ip service print where name=ssh
    # Fallback protection (if detection fails)
    # You may enhance this if needed based on your lab design
    Return    ether1


Enable Port
    [Arguments]    ${port}
    Log    Enabling port ${port}
    Execute Command    /interface ethernet enable ${port}


Disable Port
    [Arguments]    ${port}
    Log    Disabling port ${port}
    Execute Command    /interface ethernet disable ${port}


Enable Multiple Ports
    [Arguments]    @{ports}
    FOR    ${port}    IN    @{ports}
        Enable Port    ${port}
    END


Disable All Ports Except
    [Arguments]    @{allowed_ports}

    ${all_ports}=    Get All Ethernet Ports
    ${mgmt_port}=    Get SSH Management Port

    Append To List    ${allowed_ports}    ${mgmt_port}

    Log    Allowed Ports: ${allowed_ports}

    FOR    ${port}    IN    @{all_ports}
        Run Keyword If    '${port}' not in ${allowed_ports}
        ...    Disable Port    ${port}
    END


Prepare Router For PTP
    [Arguments]    ${router_name}    ${radio_port}    ${pc_port}

    # Disable all bridge ports
    Execute Command    /interface bridge port disable [find]

    # Enable required bridge ports
    Execute Command    /interface bridge port enable [find where interface="${radio_port}"]
    Execute Command    /interface bridge port enable [find where interface="${pc_port}"]

    # Ensure physical interfaces are enabled
    Execute Command    /interface enable "${radio_port}"
    Execute Command    /interface enable "${pc_port}"

    # Silent verification
    ${after}=    Execute Command    /interface bridge port print terse

    Should Contain    ${after}    ${radio_port}
    Should Contain    ${after}    ${pc_port}

    Log To Console    Config ${router_name} : PASS




Restore All Ports
    Log    Restoring all ethernet ports
    Execute Command    /interface ethernet enable [find]
