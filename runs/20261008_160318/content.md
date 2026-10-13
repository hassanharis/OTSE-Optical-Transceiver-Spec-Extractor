 




# **OP13TI8-005D** 

## **PRODUCT FEATURES** 

- Support 212.5 Gb/s Data rate per channel 

- Electrically hot-pluggable 

- Single 3.3V power supply 

- Digital Diagnostics Monitoring Interface 

- Dual MPO-12/APC optical receptacle 

- Case operating temperature range:0°C to 70°C 

- Power dissipation < 20W（Typical 18W） 


- Integrated Silicon photonics modulator chip 1310nm 

   - High-power DFB Laser / 1310nm PIN for up to 500m reach over SMF 

- Be compliant to ROHS 

## **REFERENCE STANDARD** 

- Refer to OSFP MSA rev5.0 

- Refer to OIF-CMIS rev5.2 

- Refer to IEEE 802.3dj-2024 

## **APPLICATIONS** 

##  1.6T Ethernet 

OP13TI8-005D   modules are designed for use in 1.6T Ethernet links on up to 500m of single mode fiber. Forward error correction (FEC) is required to be implemented by the host in order to ensure reliable system operation. They are compliant with the OSFP MSA, IEEE802.3dj, OIF-CMIS. 

**XGIGA Communication Technology Co.,ltd                      https://www.amphenol-cs.com/optics.html** 


## **PRODUCT SPECIFICATION** 

## I. **Absolute Maximum Ratings** 

|**Parameter**|**Symbol**|**Min.**|**Typ.**|**Max.**|**Unit**|**Note**|
|---|---|---|---|---|---|---|
|Storage Temperature|Ts|-40|-|85|ºC||
|Relative Humidity|RH|5|-|85|%||
|Power Supply Voltage|VCC|-0.5|-|3.6|V||
|Optical Receiver Damage<br>Thresholdinput|Pdmg|5.0|||dBm||



## II. **Recommended Operating Conditions** 


**----- Start of picture text -----**<br>
Parameter  Symbol Min. Typ.  Max.  Unit  Note<br>Case Operating Temperature  Tcase  0  70  ºC  Without air flow<br>Power Supply Voltage  VCC  3.135 3.3  3.465  V<br>Power Supply Current  ICC  6060  mA  When Vcc is 3.3V<br>Each channel-<br>Data Rate  BR  106.25@PAM4 GBd<br>Optical<br>Transmission Distance  TD  2  -  500  m<br>Coupled fiber  Single mode fiber  9/125um SMF<br>**----- End of picture text -----**<br>


## III. **Optical Characteristics** 


**----- Start of picture text -----**<br>
Parameter  Symbol Min  Typ  Max  Unit Note<br>Transmitter<br>106.25 ± 50<br>Signaling Speed per Lane   GBd<br>ppm<br>Modulation format  PAM4<br>Wavelength Assignment  λ 1304.5  1317.5  nm  3<br>Average Launch Power Per lane  -2.8  4.0  dBm<br>Transmit OMA per Lane(max)   4.2  dBm<br>Transmit OMA per Lane(min)<br>for max(TECQ,TDECQ)<0.9dB  -0.3<br>dBm<br>for 0.9dB≤max(TECQ,TDECQ)≤ -<br>3.4dB  1.2+max(TECQ,TDECQ)<br>Transmitter and Dispersion eye<br>closure for PAM4(TDECQ) each  TDECQ 3.4  dB<br>lane<br>**----- End of picture text -----**<br>


**XGIGA Communication Technology Co.,ltd                      https://www.amphenol-cs.com/optics.html** 



 


**----- Start of picture text -----**<br>
TECQ(max)  3.4  dB<br>│TDECQ-TECQ│(max)  2.5  dB<br>Transmitter overshoot and<br>22  %<br>undershoot(max)<br>SMSR  30  dB<br>Optical Extinction Ratio  ER  3.5  dB<br>Average launch Power off per lane  Poff  -15  dBm<br>RINxxOMA (max)  RIN  -139  dB/Hz<br>Optical return loss tolerance(max)  21.4  dB<br>Transmitter Reflectance  Tr  -26  dB<br>Receiver<br>106.25 ±<br>Signaling Speed per Lane   GBd<br>50ppm<br>Modulation format  PAM4<br>Wavelength Assignment  λ 1304.5  1317.5  nm  3<br>Damage Threshold per Lane  5.0  dBm 1<br>Receive Power (OMA) per Lane  ROMA 4.2  dBm<br>Average Input Power per Channel  RXPx  -5.8  4.0  dBm<br>Receiver Sensitivity (OMA) per<br>Lane  -3.4<br>RXsens  dBm 2<br>-<br>for TECQ<0.9 dB<br>for 0.9dB≤TECQ≤SECQ 4.3+TECQ<br>Stressed receiver<br>-0.9  dBm 3<br>sensitivity(OMAouter),each lane<br>Stressed eye closure receiver<br>3.4  dB  4<br>sensitivity test<br>OMAouter of each aggressor lane  2.9  dBm<br>Receiver Reflectance   Rr  -26  dB<br>**----- End of picture text -----**<br>


## **Notes:** 

1. The receiver shall be able to tolerate, without damage, continuous exposure to an optical input signal having this average power level. 

- -4 

- 2. Measured with a PRBS31Q test pattern, BER@2.4*10 . 

3. The wavelength assignment is suitable for all channels. 

**XGIGA Communication Technology Co.,ltd                      https://www.amphenol-cs.com/optics.html** 



 

## **IV.Link Power Budget** 

|**IV. Link Power Budget**||||
|---|---|---|---|
|**Parameter**|**Typ**|**Unit**|**NOTE**|
|Power budget(for maximum TDECQ)|6.5|dB||
|Operating distance|500|m||
|Channel insertion loss|3|dB||
|Allocation for penalties(for maximum TDECQ)|3.5|dB||






## **Notes:** 

1. OSFP uses common ground (GND) for all signals and supply (power). All are common within the OSFP module and all module voltages are referenced to this potential unless otherwise noted. Connect these directly to the host board signalcommon ground plane. 

2. Open-Drain with pull-up resistor on Host. 

**XGIGA Communication Technology Co.,ltd                      https://www.amphenol-cs.com/optics.html** 

 



## **VI. Host - Transceiver Interface Block Diagram** 


**----- Start of picture text -----**<br>
1<br>**----- End of picture text -----**<br>


Figure2--- Host - Transceiver Interface Block Diagram 

## **Notes:** 

1. LRO module does not have a RX CDR 

**XGIGA Communication Technology Co.,ltd                      https://www.amphenol-cs.com/optics.html** 




**----- Start of picture text -----**<br>
Rev 1.0<br>**----- End of picture text -----**<br>


## **VII. Mechanical Specifications** 





**----- Start of picture text -----**<br>
Units in mm<br>Dual MPO-12 connector<br>**----- End of picture text -----**<br>



Figure3--- Mechanical Specifications 

## **VIII. Regulatory Compliance** 


**----- Start of picture text -----**<br>
Feature  Reference  Performance<br>Electrostatic discharge（ESD） IEC/EN 61000-4-2  Compatible with standards<br>FCC Part 15 Class B /EN 55022 Class B<br>Electromagnetic Interference (EMI)  Compatible with standards<br>(CISPR 22A)<br>FDA 21CFR 1040.10, 1040.11 IEC/EN<br>Laser Eye Safety  Class 1 laser product<br>60825-1, 2<br>Component Recognition  IEC/EN 62368-1, UL62368-1  Compatible with standards<br>ROHS  2011/65/EU and 2015/863/EU  Compatible with standards<br>REACH  Regulation(EC) No.1907/2006  Compatible with standards<br>**----- End of picture text -----**<br>


## **Warnings** 

**XGIGA Communication Technology Co.,ltd                      https://www.amphenol-cs.com/optics.html** 


Handling Precautions: This device is susceptible to damage as a result of electrostatic discharge (ESD). A static free environment is highly recommended. Follow guidelines according to proper ESD procedures. Laser Safety: Radiation emitted by laser devices can be dangerous to human eyes. Avoid eye exposure to direct or indirect radiation. 

## **Appendix A. Document Revision** 

|**Version No.**|**Date**|**Description**|
|---|---|---|
|1.0|2024-7-24|Draft version|



**XGIGA Communication Technology Co.,ltd                      https://www.amphenol-cs.com/optics.html** 

