*** Settings ***
Library    SSHLibrary
Library    Collections
Library    OperatingSystem
Library    String
Library    DateTime
Library    Process
Variables  ${CURDIR}/../inventory.yaml
Variables  ${CURDIR}/../mikrotik/ptp_setups.yaml
Resource   ${CURDIR}/../resources/connection_keywords.robot
Resource   ${CURDIR}/../resources/mikrotik_keywords.robot


*** Variables ***
${MIN_EXPECTED_MBPS}    100


*** Keywords ***

# ===========================
# 🔥 IPERF ENGINE
# ===========================

Start Iperf Server
    [Arguments]    ${side}

    Log To Console    Starting iperf server on ${side}

    Connect To Device    ubuntu    ${side}
    Execute Command    pkill iperf3
    Execute Command    iperf3 -s -D
    Disconnect Device    ${side}

    Sleep    2s

Stop Iperf Server
    [Arguments]    ${side}

    Log To Console    Stopping iperf server on ${side}

    Connect To Device    ubuntu    ${side}
    Execute Command    pkill iperf3
    Disconnect Device    ${side}

Execute Iperf Client
    [Arguments]    ${side}    ${command}

    Log To Console    Executing on ${side}: ${command}

    Connect To Device    ubuntu    ${side}
    ${output}=    Execute Command    ${command}
    Disconnect Device    ${side}

    RETURN    ${output}



Run Iperf TCP
    [Arguments]    ${src}    ${dst}    ${streams}=4

    Start Iperf Server    ${dst}

    ${server_ip}=    Get Device IP    ${dst}

    ${cmd}=    Set Variable
    ...    iperf3 -c ${server_ip} -i1 -t 60 -P ${streams} -J

    ${output}=    Execute Iperf Client    ${src}    ${cmd}

    Stop Iperf Server    ${dst}

    RETURN    ${output}



Run Iperf TCP Bidirectional
    [Arguments]    ${src}    ${dst}    ${streams}=4

    Start Iperf Server    ${dst}

    ${server_ip}=    Get Device IP    ${dst}

    ${cmd}=    Set Variable
    ...    iperf3 -c ${server_ip} -i1 -t 60 -P ${streams} --bidir -J

    ${output}=    Execute Iperf Client    ${src}    ${cmd}

    Stop Iperf Server    ${dst}

    RETURN    ${output}



Run Iperf UDP
    [Arguments]    ${src}    ${dst}

    Start Iperf Server    ${dst}

    ${server_ip}=    Get Device IP    ${dst}

    ${cmd}=    Set Variable
    ...    iperf3 -c ${server_ip} -i1 -u -b 2G -t 60 -J

    ${output}=    Execute Iperf Client    ${src}    ${cmd}

    Stop Iperf Server    ${dst}

    RETURN    ${output}


Run Iperf UDP Bidirectional
    [Arguments]    ${src}    ${dst}

    Start Iperf Server    ${dst}

    ${server_ip}=    Get Device IP    ${dst}

    ${cmd}=    Set Variable
    ...    iperf3 -c ${server_ip} -u -i1 -b 2G -t 60 --bidir -J

    ${output}=    Execute Iperf Client    ${src}    ${cmd}

    Stop Iperf Server    ${dst}

    RETURN    ${output}

# =====================================
# 🔥 GET DEVICE IP
# =====================================

Get Device IP
    [Arguments]    ${side}

    ${ubuntu}=    Get From Dictionary    ${devices}    ubuntu
    ${node}=      Get From Dictionary    ${ubuntu}    ${side}
    ${ip}=        Get From Dictionary    ${node}      test_host

    RETURN    ${ip}

Initialize Selected Models


    IF    '${PTP_SETUP}' == ''
        Fail    PTP_SETUP not provided. Use: -v PTP_SETUP:V5000POP_V3000CN
    END

    ${setup}=    Get From Dictionary    ${ptp_setups}    ${PTP_SETUP}

    ${pop}=    Get From Dictionary    ${setup}    pop_side
    ${cn}=     Get From Dictionary    ${setup}    cn_side

    ${pop_device}=    Get From Dictionary    ${pop}    device
    ${cn_device}=     Get From Dictionary    ${cn}    device

    ${POP_MODEL}=    Evaluate    '${pop_device}'.replace('POP','').replace('CN','')
    ${DN_MODEL}=     Evaluate    '${cn_device}'.replace('POP','').replace('CN','')

    Set Suite Variable    ${POP_MODEL}
    Set Suite Variable    ${DN_MODEL}

    Log To Console    Auto-detected PoP Model: ${POP_MODEL}
    Log To Console    Auto-detected DN Model: ${DN_MODEL}


Initialize Run Directory
    ${timestamp}=    Evaluate    __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')

    ${base_dir}=    Set Variable    results
    Create Directory    ${base_dir}

    ${model_dir}=    Set Variable    ${base_dir}/${PTP_SETUP}
    Create Directory    ${model_dir}

    # If RESULT_DIR already provided externally, use it
    ${has_external}=    Run Keyword And Return Status    Variable Should Exist    ${RESULT_DIR}

    IF    ${has_external}
        Log To Console    Using external result directory: ${RESULT_DIR}
        RETURN
    END

    ${run_dir}=    Set Variable    ${model_dir}/${timestamp}
    Create Directory    ${run_dir}

    Set Suite Variable    ${RESULT_DIR}    ${run_dir}

    Log To Console    Results folder created: ${run_dir}


Lock Bridge Ports For PTP

    Log To Console    ===== Locking Bridge Ports For ${PTP_SETUP} =====

    ${setup}=    Get From Dictionary    ${ptp_setups}    ${PTP_SETUP}

    ${pop_side}=    Get From Dictionary    ${setup}    pop_side
    ${cn_side}=     Get From Dictionary    ${setup}    cn_side

    ${pop_router}=    Get From Dictionary    ${pop_side}    router
    ${cn_router}=     Get From Dictionary    ${cn_side}    router

    ${pop_radio_port}=    Get From Dictionary    ${pop_side}    port
    ${cn_radio_port}=     Get From Dictionary    ${cn_side}    port

    ${pop_pc}=    Get From Dictionary    ${traffic_pc}    pop_side
    ${cn_pc}=     Get From Dictionary    ${traffic_pc}    cn_side

    ${pop_pc_port}=    Get From Dictionary    ${pop_pc}    port
    ${cn_pc_port}=     Get From Dictionary    ${cn_pc}    port

    # -------------------------
    # PoP Router
    # -------------------------
    Log To Console    ---- Configuring ${pop_router} ----
    Connect To Device    mikrotik    ${pop_router}

    Execute Command    /interface bridge port disable [find]

    Execute Command    /interface bridge port enable [find where interface="${pop_radio_port}"]
    Execute Command    /interface bridge port enable [find where interface="${pop_pc_port}"]

    Verify Bridge Port Running    ${pop_radio_port}
    Verify Bridge Port Running    ${pop_pc_port}

    Disconnect Device    ${pop_router}

    # -------------------------
    # CN Router
    # -------------------------
    Log To Console    ---- Configuring ${cn_router} ----
    Connect To Device    mikrotik    ${cn_router}

    Execute Command    /interface bridge port disable [find]

    Execute Command    /interface bridge port enable [find where interface="${cn_radio_port}"]
    Execute Command    /interface bridge port enable [find where interface="${cn_pc_port}"]

    Verify Bridge Port Running    ${cn_radio_port}
    Verify Bridge Port Running    ${cn_pc_port}

    Disconnect Device    ${cn_router}

Verify Bridge Port Running
    [Arguments]    ${port}

    ${output}=    Execute Command    /interface bridge port print where interface="${port}"

    Should Contain    ${output}    ${port}
    Should Not Contain    ${output}    X



Log Raw Results
    [Arguments]    
    ...    ${test_name}    
    ...    ${result}    
    ...    ${channel}    
    ...    ${tdd}    
    ...    ${mcs}    
    ...    ${pop_version}=${POP_VERSION}    
    ...    ${dn_version}=${DN_VERSION}

    ${json_file}=    Set Variable    ${RESULT_DIR}/${test_name}.json
    Create File    ${json_file}    ${result}

    ${raw_file}=    Set Variable    ${RESULT_DIR}/raw_${test_name}.txt
    Create File    ${raw_file}    ${result}

    Log To Console    Saved JSON: ${json_file}
    Log To Console    Saved RAW: ${raw_file}

    ${tdd_clean}=    Replace String    ${tdd}    /    -

    ${channel_dir}=    Set Variable    ${RESULT_DIR}/${channel}
    Create Directory    ${channel_dir}

    ${tdd_dir}=    Set Variable    ${channel_dir}/TDD ${tdd_clean}
    Create Directory    ${tdd_dir}

    ${mcs_dir}=    Set Variable    ${tdd_dir}/MCS${mcs}
    Create Directory    ${mcs_dir}

    ${graph_file}=    Set Variable    ${mcs_dir}/${test_name}_graph.png

    ${plot_script}=    Set Variable    ${CURDIR}/../performance/plot_iperf.py

    ${result}=    Run Process
    ...    py
    ...    ${plot_script}
    ...    ${json_file}
    ...    ${graph_file}
    ...    stdout=PIPE
    ...    stderr=PIPE

    ${avg_output}=    Set Variable    ${result.stdout}

    Log To Console    ${avg_output}
    Log    ${avg_output}

    ${has_average}=    Run Keyword And Return Status
    ...    Should Contain
    ...    ${avg_output}
    ...    Average

    IF    not ${has_average}
        Fail    No throughput detected. Traffic did not pass.
    END

    ${sent_exists}=    Run Keyword And Return Status
    ...    Should Contain
    ...    ${avg_output}
    ...    Average Sent Throughput

    ${recv_exists}=    Run Keyword And Return Status
    ...    Should Contain
    ...    ${avg_output}
    ...    Average Received Throughput

    IF    ${sent_exists}
        ${sent_value}=    Evaluate
        ...    float("""${avg_output}""".split("Average Sent Throughput:")[1].split("Mbps")[0].strip())
    ELSE
        ${sent_value}=    Evaluate
        ...    float("""${avg_output}""".split("Average Throughput:")[1].split("Mbps")[0].strip())
    END

    Log To Console    Sent Avg Mbps: ${sent_value}

    IF    ${recv_exists}
        ${recv_value}=    Evaluate
        ...    float("""${avg_output}""".split("Average Received Throughput:")[1].split("Mbps")[0].strip())
        Log To Console    Received Avg Mbps: ${recv_value}
    ELSE
        ${recv_value}=    Set Variable    0
    END

    ${sent_check}=    Run Keyword And Return Status
    ...    Should Be True
    ...    ${sent_value} >= ${MIN_EXPECTED_MBPS}

    ${recv_check}=    Set Variable    True

    IF    ${recv_exists}
        ${recv_check}=    Run Keyword And Return Status
        ...    Should Be True
        ...    ${recv_value} >= ${MIN_EXPECTED_MBPS}
    END

    ${status}=    Set Variable    PASS

    IF    not ${sent_check}
        ${status}=    Set Variable    FAIL
    END

    IF    not ${recv_check}
        ${status}=    Set Variable    FAIL
    END

    IF    ${recv_exists}
        Should Be True
        ...    ${recv_value} >= ${MIN_EXPECTED_MBPS}
        ...    Received throughput ${recv_value} Mbps is below expected ${MIN_EXPECTED_MBPS} Mbps
    END

    Log To Console    Graph saved: ${graph_file}
    Log    <img src="${graph_file}" width="800px">    html=True

    ${timestamp}=    Get Time    result_format=%Y-%m-%d %H:%M:%S

    ${status}=    Set Variable    PASS
    ${status_check}=    Run Keyword And Return Status
    ...    Should Be True
    ...    ${sent_value} >= ${MIN_EXPECTED_MBPS}

    IF    not ${status_check}
        ${status}=    Set Variable    FAIL
    END

    IF    ${recv_exists}
        ${recv_check}=    Run Keyword And Return Status
        ...    Should Be True
        ...    ${recv_value} >= ${MIN_EXPECTED_MBPS}

        IF    not ${recv_check}
            ${status}=    Set Variable    FAIL
        END
    END


    # Extract run folder name (example: 20260224_172045)
    ${run_id}=    Evaluate    __import__('os').path.basename(r'''${RESULT_DIR}''')
    
    ${csv_file}=    Set Variable    dashboard_data.csv

    # ===========================
    # UPDATED ROW WITH BOARD MODEL
    # ===========================

    ${row}=    Set Variable
    ...    ${timestamp},${PTP_SETUP},${run_id},${channel},${tdd},${mcs},${test_name},${sent_value},${recv_value},${status},${pop_version},${dn_version}\n

    ${file_exists}=    Run Keyword And Return Status    OperatingSystem.File Should Exist    ${csv_file}
    
    IF    not ${file_exists}
        Create File
        ...    ${csv_file}
        ...    timestamp,board_model,run_id,channel,tdd,mcs,test_name,sent_avg,recv_avg,status,pop_version,dn_version\n
    END

    Append To File    ${csv_file}    ${row}

    Log To Console    Dashboard updated: ${csv_file}
