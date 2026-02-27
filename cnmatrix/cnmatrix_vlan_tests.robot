*** Settings ***
Resource    ../../resources/common_keywords.robot
Library    Collections

*** Test Cases ***
Add VLAN To cnMatrix
    Load Inventory
    ${switch}=    Set Variable    ${DEVICES}[cnmatrix][0]
    Open Telnet To Device    ${switch}
    Write    configure terminal
    Write    vlan 10
    Write    name VLAN10-Test
    Write    end
    ${output}=    Read Until Prompt
    Should Contain    VLAN10-Test
    Write    configure terminal
    Write    interface GigabitEthernet 0/1
    Write    switchport mode access
    Write    switchport access vlan 10
    Write    description Test-Port
    Write    no shutdown  # Enable
    Write    end
    Close Connection
