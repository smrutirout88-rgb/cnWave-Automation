*** Settings ***
Resource    cnwave_keywords.robot
Resource    ../resources/iperf_keywords.robot
Variables   ../inventory.yaml
Variables   ../mikrotik/ptp_setups.yaml

Suite Setup    Full Pre-Setup

*** Variables ***
${CB_NAME}     CB2


*** Test Cases ***

TC01 - CB2 | TDD 50-50 | MCS 12
    Run CB2 Scenario    0    50-50    12    9

TC02 - CB2 | TDD 50-50 | MCS 9
    Run CB2 Scenario    0    50-50    9     9

TC03 - CB2 | TDD 50-50 | MCS 2
    Run CB2 Scenario    0    50-50    2     9


*** Keywords ***

Full Pre-Setup
    Log To Console    ===== Starting Full Environment Setup =====

    Lock Bridge Ports For PTP

    # Get selected PTP setup
    ${setup}=    Get From Dictionary    ${ptp_setups}    ${PTP_SETUP}

    # Extract POP device (example: V5000POP)
    ${pop_side}=    Get From Dictionary    ${setup}    pop_side
    ${pop_device}=    Get From Dictionary    ${pop_side}    device
    
    Set Suite Variable    ${POP_NODE_NAME}    ${pop_device}

    # Extract model from device name
    # V5000POP -> V5000
    ${pop_model}=    Replace String    ${pop_device}    POP    ${EMPTY}

    # Convert to lowercase
    ${pop_model_lower}=    Convert To Lowercase    ${pop_model}

    # Build public controller key
    ${controller_key}=    Set Variable    pop_${pop_model_lower}

    Log To Console    Controller Key: ${controller_key}

    # Fetch controller details
    ${controller}=    Get From Dictionary    ${public_controllers}    ${controller_key}

    ${HOST}=        Get From Dictionary    ${controller}    host
    ${PORT}=        Get From Dictionary    ${controller}    port
    ${USERNAME}=    Get From Dictionary    ${controller}    username
    ${PASSWORD}=    Get From Dictionary    ${controller}    password

    Log To Console    Connecting to: ${HOST}:${PORT}

    Connect To Controller    ${HOST}    ${USERNAME}    ${PASSWORD}    ${PORT}

    Initialize Selected Models
    Initialize Run Directory

Run CB2 Scenario
    [Arguments]    ${tdd_value}    ${tdd_label}    ${mcs_value}    ${channel}

    Log To Console    ========================================================
    Log To Console    Running ${CB_NAME} | TDD ${tdd_label} | MCS ${mcs_value}
    Log To Console    ========================================================

    # Step 1 - Initial Link Validation
    Log To Console    Step-1: Validate Initial Link
    Wait For Initial Link    90

    # Step 2 - Ensure MCS
    Log To Console    Step-2: Ensure MCS = ${mcs_value}
    Ensure MCS Config    ${mcs_value}

    # Step 3 - Change Channel
    Log To Console    Step-3: Change Channel to ${channel}
    Set Channel Config    ${channel}

    # Step 4 - Validate Link After Channel Change
    Log To Console    Step-4: Validate Link After Channel Change
    Wait For Initial Link    120

    # Step 5 - Run Traffic
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

