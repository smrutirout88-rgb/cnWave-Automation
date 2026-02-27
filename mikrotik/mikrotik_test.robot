*** Settings ***
Resource    ../resources/common_keywords.robot
Library     SSHLibrary
Library     Collections
Library    String
Test Timeout    5 minutes

*** Variables ***
${DEVICE_TYPE}    mikrotik
${DEVICE_NAME}    router1

*** Test Cases ***

TC01_Bridge_Port_Enable_Disable
    [Documentation]    Detect bridge port and toggle it
    [Tags]    bridge    validation

    Connect To Device    ${DEVICE_TYPE}    ${DEVICE_NAME}

    ${bridge_ports}=    Execute Command    /interface bridge port print
    Log    <b>Bridge Ports:</b>\n${bridge_ports}    html=True
    Should Not Be Empty    ${bridge_ports}

    ${lines}=    Split To Lines    ${bridge_ports}
    ${port}=    Set Variable    ${EMPTY}

    FOR    ${line}    IN    @{lines}
        ${parts}=    Split String    ${line}
        Run Keyword If    ${len(${parts})} > 2    Set Variable    ${port}    ${parts}[2]
        Run Keyword If    '${port}' != ''    Exit For Loop
    END

    Should Not Be Empty    ${port}
    Log    <b>Selected Bridge Port:</b> ${port}

    Execute Command    /interface bridge port disable [find interface=${port}]
    Sleep    2s

    ${status}=    Execute Command    /interface bridge port print detail where interface=${port}
    Log    <b>Status After Disable:</b>\n${status}    html=True
    Should Contain    ${status}    disabled=yes

    Execute Command    /interface bridge port enable [find interface=${port}]
    Sleep    2s

    ${status}=    Execute Command    /interface bridge port print detail where interface=${port}
    Log    <b>Status After Enable:</b>\n${status}    html=True
    Should Not Contain    ${status}    disabled=yes

    Disconnect Device

TC02_Add_Free_Port_To_Bridge_And_Verify
    [Documentation]    Find free ethernet port, add to bridge, verify and cleanup
    [Tags]    bridge    dynamic

    Connect To Device    ${DEVICE_TYPE}    ${DEVICE_NAME}

    ${bridge}=    Set Variable    bridge

    ${all_ports}=    Execute Command    /interface print as-value where type=ether
    ${bridge_ports}=    Execute Command    /interface bridge port print as-value

    ${lines}=    Split To Lines    ${all_ports}
    ${selected_port}=    Set Variable    ${EMPTY}

    FOR    ${line}    IN    @{lines}
        ${exists}=    Run Keyword And Return Status
        ...    Should Contain
        ...    ${bridge_ports}
        ...    ${line}

        IF    not ${exists}
            ${parts}=    Split String    ${line}    =
            ${selected_port}=    Set Variable    ${parts}[1]
            Exit For Loop
        END
    END

    Should Not Be Empty    ${selected_port}
    Log    Selected Free Port: ${selected_port}

    Execute Command    /interface bridge port add bridge=${bridge} interface=${selected_port} comment=test-port
    Sleep    2s

    ${after_add}=    Execute Command    /interface bridge port print as-value
    Should Contain    ${after_add}    ${selected_port}
    Should Contain    ${after_add}    test-port

    Execute Command    /interface bridge port remove [find interface=${selected_port}]
    Sleep    2s

    Disconnect Device





