*** Settings ***
Library    BuiltIn

*** Variables ***
${CLIENT}    ${None}

*** Keywords ***

Connect To Controller
    [Arguments]    ${host}    ${username}    ${password}    ${port}=3443

    ${client}=    Evaluate
    ...    __import__("libraries.cnwave.client").cnwave.client.CnWaveClient("${host}", "${username}", "${password}", port=${port}, verify_ssl=False)
    ...    modules=libraries.cnwave.client

    Set Suite Variable    ${CLIENT}    ${client}

    Log To Console    Connected to CNWave Controller at ${host}:${port}


Get Topology
    ${topology}=    Call Method    ${CLIENT}    get_topology
    RETURN    ${topology}


Get Nodes
    ${nodes}=    Call Method    ${CLIENT}    get_nodes
    RETURN    ${nodes}


Get Links
    ${links}=    Call Method    ${CLIENT}    get_links
    RETURN    ${links}

Get Current Tdd
    ${overrides}=    Call Method    ${CLIENT}    get_network_overrides_parsed
    Should Not Be Empty    ${overrides}

    ${radio}=    Get From Dictionary    ${overrides}    radioParamsBase
    ${fw}=       Get From Dictionary    ${radio}        fwParams
    ${tdd}=      Get From Dictionary    ${fw}           tddSlotRatio

    RETURN    ${tdd}


Set Tdd
    [Arguments]    ${value}
    Call Method    ${CLIENT}    update_tdd_slot_ratio    ${value}

Get Current Mcs
    ${overrides}=    Call Method    ${CLIENT}    get_node_overrides_parsed
    Should Not Be Empty    ${overrides}

    ${pop}=     Get From Dictionary    ${overrides}    PoP
    ${link}=    Get From Dictionary    ${pop}          linkParamsBase
    ${fw}=      Get From Dictionary    ${link}         fwParams

    ${exists}=    Run Keyword And Return Status
    ...    Dictionary Should Contain Key
    ...    ${fw}
    ...    laMaxMcs

    IF    not ${exists}
        Log To Console    MCS override not present. Returning default 12.
        RETURN    12
    END

    ${mcs}=     Get From Dictionary    ${fw}    laMaxMcs
    RETURN    ${mcs}


Set Mcs
    [Arguments]    ${value}
    Call Method    ${CLIENT}    update_mcs    ${value}

Wait For Link Active
    [Arguments]    ${timeout}=90
    Call Method    ${CLIENT}    wait_for_link_active    ${timeout}

Wait For Initial Link
    [Arguments]    ${timeout}=90

    Log To Console    Waiting for initial link...

    Wait For Link Active    ${timeout}

    Log To Console    Initial link is active
    

Ensure TDD Config
    [Arguments]    ${expected}

    ${current}=    Get Current Tdd
    Log To Console    Current TDD: ${current}

    Run Keyword If    ${current} != ${expected}
    ...    Change TDD And Wait Recovery    ${expected}
    ...  ELSE
    ...    Log To Console    TDD already correct. No change required.


Change TDD And Wait Recovery
    [Arguments]    ${value}

    Log To Console    Changing TDD to ${value}
    Set Tdd    ${value}

    Log To Console    Waiting for link stabilization...

    ${status}=    Call Method
    ...    ${CLIENT}
    ...    wait_for_link_stable
    ...    300
    ...    5
    ...    60

    Run Keyword If    not ${status}
    ...    Fail    Link did not stabilize after TDD change

    Log To Console    Link is stable after TDD change


Ensure MCS Config
    [Arguments]    ${expected}

    Log To Console    Ensuring MCS is ${expected}

    ${status}=    Call Method    ${CLIENT}    update_mcs    ${expected}

    Log To Console    Waiting for link recovery after MCS change

    ${link_status}=    Run Keyword And Return Status
    ...    Wait For Link Active    90

    Run Keyword Unless    ${link_status}
    ...    Fail    Link not active after MCS config change

    Log To Console    Link stable after MCS check


Change MCS And Wait Recovery
    [Arguments]    ${value}

    Log To Console    Changing MCS to ${value}
    Set Mcs    ${value}

    Log To Console    Waiting for link recovery after MCS change

    ${status}=    Run Keyword And Return Status
    ...    Wait For Link Active    90

    Run Keyword If    not ${status}
    ...    Fail    Link not active after MCS config change

    Log To Console    Link recovered after MCS change


Get POP And DN Versions
    [Arguments]    ${pop_name}    ${dn_name}

    ${pop_version}    ${dn_version}=    
    ...    Call Method    
    ...    ${CLIENT}    
    ...    get_pop_dn_versions    
    ...    ${pop_name}    
    ...    ${dn_name}

    Log To Console    POP Version: ${pop_version}
    Log To Console    DN Version:  ${dn_version}

    Set Suite Variable    ${POP_VERSION}    ${pop_version}
    Set Suite Variable    ${DN_VERSION}     ${dn_version}

    RETURN    ${pop_version}    ${dn_version}

Get Node Info
    ${info}=    Call Method    ${CLIENT}    get_node_info
    Log To Console    ${info}
    RETURN    ${info}



