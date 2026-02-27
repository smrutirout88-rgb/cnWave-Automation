*** Settings ***
Resource    cnwave_keywords.robot
Resource    ../resources/iperf_keywords.robot
Variables   ../inventory.yaml
Variables   ../mikrotik/ptp_setups.yaml

Suite Setup       Combined Suite Setup
Suite Teardown    Print Suite Execution Time
Test Setup        Record Test Start Time
Test Teardown     Print Test Execution Time


*** Variables ***
${CB_NAME}     CB1

${SUITE_START_TIME}    ${None}
${TEST_START_TIME}     ${None}


*** Test Cases ***

TC01 - CB1 | TDD 50-50 | MCS 12
    Run CB1 Scenario    0    50-50    12

TC02 - CB1 | TDD 50-50 | MCS 9
    Run CB1 Scenario    0    50-50    9

TC03 - CB1 | TDD 50-50 | MCS 2
    Run CB1 Scenario    0    50-50    2


TC04 - CB1 | TDD 75-25 | MCS 12
    Run CB1 Scenario    3    75-25    12

TC05 - CB1 | TDD 75-25 | MCS 9
    Run CB1 Scenario    3    75-25    9

TC06 - CB1 | TDD 75-25 | MCS 2
    Run CB1 Scenario    3    75-25    2


TC07 - CB1 | TDD 30-70 | MCS 12
    Run CB1 Scenario    5    30-70    12

TC08 - CB1 | TDD 30-70 | MCS 9
    Run CB1 Scenario    5    30-70    9

TC09 - CB1 | TDD 30-70 | MCS 2
    Run CB1 Scenario    5    30-70    2


*** Keywords ***

Full Pre-Setup
    Log To Console    ===== Starting Full Environment Setup =====

    Lock Bridge Ports For PTP

    # Get selected PTP setup
    ${setup}=    Get From Dictionary    ${ptp_setups}    ${PTP_SETUP}

    # --------------------------------------------------
    # Extract POP device
    # --------------------------------------------------
    ${pop_side}=    Get From Dictionary    ${setup}    pop_side
    ${pop_device}=    Get From Dictionary    ${pop_side}    device
    Set Suite Variable    ${POP_NODE_NAME}    ${pop_device}
    Log To Console        POP Node: ${POP_NODE_NAME}

    # --------------------------------------------------
    # Extract CN device  (FIXED: uses cn_side)
    # --------------------------------------------------
    ${cn_side}=     Get From Dictionary    ${setup}    cn_side
    ${cn_device}=   Get From Dictionary    ${cn_side}    device
    Set Suite Variable    ${DN_NODE_NAME}    ${cn_device}
    Log To Console        DN Node: ${DN_NODE_NAME}

    # --------------------------------------------------
    # Extract model from device name
    # V5000POP -> V5000
    # --------------------------------------------------
    ${pop_model}=    Replace String    ${pop_device}    POP    ${EMPTY}

    # Convert to lowercase
    ${pop_model_lower}=    Convert To Lowercase    ${pop_model}

    # Build public controller key
    ${controller_key}=    Set Variable    pop_${pop_model_lower}

    Log To Console    Controller Key: ${controller_key}

    # --------------------------------------------------
    # Fetch controller details
    # --------------------------------------------------
    ${controller}=    Get From Dictionary    ${public_controllers}    ${controller_key}

    ${HOST}=        Get From Dictionary    ${controller}    host
    ${PORT}=        Get From Dictionary    ${controller}    port
    ${USERNAME}=    Get From Dictionary    ${controller}    username
    ${PASSWORD}=    Get From Dictionary    ${controller}    password

    Log To Console    Connecting to: ${HOST}:${PORT}

    Connect To Controller    ${HOST}    ${USERNAME}    ${PASSWORD}    ${PORT}

    ${node_info}=    Get Node Info

    # --------------------------------------------------
    # Fetch software versions once per suite
    # --------------------------------------------------
    ${pop_version}    ${dn_version}=    
    ...    Call Method    
    ...    ${CLIENT}    
    ...    get_pop_dn_versions    

    Set Suite Variable    ${POP_VERSION}    ${pop_version}
    Set Suite Variable    ${DN_VERSION}     ${dn_version}

    Log To Console    POP Software Version: ${POP_VERSION}    stream=stdout
    Log To Console    POP Software Version: ${DN_VERSION}    stream=stdout

    Initialize Selected Models
    Initialize Run Directory

Combined Suite Setup
    Record Suite Start Time
    Full Pre-Setup


Record Suite Start Time
    ${start}=    Get Time    epoch
    Set Suite Variable    ${SUITE_START_TIME}    ${start}

    ${human}=    Get Time
    Log To Console    \n========== SUITE STARTED ==========
    Log To Console    Start Time: ${human}
    Log    Suite Start Time: ${human}    WARN


Print Suite Execution Time
    ${end}=    Get Time    epoch
    ${human_end}=    Get Time

    ${duration}=    Evaluate    ${end} - ${SUITE_START_TIME}
    ${minutes}=     Evaluate    int(${duration} // 60)
    ${seconds}=     Evaluate    int(${duration} % 60)

    Log To Console    \n========== SUITE COMPLETED ==========
    Log To Console    End Time: ${human_end}
    Log To Console    Total Execution Time: ${minutes} min ${seconds} sec

    Log    Suite End Time: ${human_end}    WARN
    Log    Total Execution Time: ${minutes} min ${seconds} sec    WARN


Record Test Start Time
    ${start}=    Get Time    epoch
    Set Test Variable    ${TEST_START_TIME}    ${start}

    ${human}=    Get Time
    Log To Console    \n----- TEST STARTED -----
    Log To Console    ${TEST NAME} at ${human}
    Log    Test Start Time: ${human}


Print Test Execution Time
    ${end}=    Get Time    epoch
    ${human_end}=    Get Time

    ${duration}=    Evaluate    ${end} - ${TEST_START_TIME}
    ${seconds}=     Evaluate    round(${duration}, 2)

    Log To Console    ${TEST NAME} completed at ${human_end}
    Log To Console    Test Duration: ${seconds} seconds

    Log    Test End Time: ${human_end}
    Log    Test Duration: ${seconds} seconds


Run CB1 Scenario
    [Arguments]    ${tdd_value}    ${tdd_label}    ${mcs_value}

    Log To Console    ========================================================
    Log To Console    Running ${CB_NAME} | TDD ${tdd_label} | MCS ${mcs_value}
    Log To Console    ========================================================

    # Step 1 - Initial Link Validation
    Wait For Initial Link    90

    # Step 2 - Ensure TDD
    Ensure TDD Config    ${tdd_value}

    # Step 3 - Ensure MCS
    Ensure MCS Config    ${mcs_value}

    # Step 4 - Run Traffic
    ${result}=    Run Iperf TCP    pop    dn    streams=4
    Log Raw Results    TCP-Downlink-4Stream    ${result}    ${CB_NAME}    ${tdd_label}    ${mcs_value}

    ${result}=    Run Iperf TCP    dn    pop    streams=4
    Log Raw Results    TCP-Uplink-4Stream    ${result}  ${CB_NAME}    ${tdd_label}    ${mcs_value}

    ${result}=    Run Iperf TCP Bidirectional    pop    dn    streams=4
    Log Raw Results    TCP-Bidirectional-4Stream    ${result}   ${CB_NAME}    ${tdd_label}    ${mcs_value}


    ${result}=    Run Iperf TCP    pop    dn    streams=1
    Log Raw Results    TCP-Downlink-1Stream    ${result}    ${CB_NAME}    ${tdd_label}    ${mcs_value}

    ${result}=    Run Iperf TCP    dn    pop    streams=1
    Log Raw Results    TCP-Uplink-1Stream    ${result}  ${CB_NAME}    ${tdd_label}    ${mcs_value}

    ${result}=    Run Iperf TCP Bidirectional    pop    dn    streams=1
    Log Raw Results    TCP-Bidirectional-1Stream    ${result}   ${CB_NAME}    ${tdd_label}    ${mcs_value}


    ${result}=    Run Iperf UDP    pop    dn
    Log Raw Results    UDP-Downlink    ${result}    ${CB_NAME}    ${tdd_label}    ${mcs_value}

    ${result}=    Run Iperf UDP    dn    pop
    Log Raw Results    UDP-Uplink    ${result}  ${CB_NAME}    ${tdd_label}    ${mcs_value}

    ${result}=    Run Iperf UDP Bidirectional    pop    dn
    Log Raw Results    UDP-Bidirectional    ${result}   ${CB_NAME}    ${tdd_label}    ${mcs_value}

