# <img src="images/icon.png" width="40"> Synology iperf3 Speedtest

<a href="https://github.com/007revad/Synology_iperf3_Speedtest/releases"><img src="https://img.shields.io/github/release/007revad/Synology_iperf3_Speedtest.svg"></a>
[![Github Releases](https://img.shields.io/github/downloads/007revad/Synology_iperf3_Speedtest/total.svg)](https://github.com/007revad/Synology_iperf3_Speedtest/releases)
![Badge](https://hitscounter.dev/api/hit?url=https%3A%2F%2Fgithub.com%2F007revad%2FSynology_iperf3_Speedtest&label=Visitors&icon=github&color=%23198754&message=&style=flat&tz=Australia%2FSydney)
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/paypalme/007revad)
[![](https://img.shields.io/static/v1?label=Sponsor&message=%E2%9D%A4&logo=GitHub&color=%23fe8e86)](https://github.com/sponsors/007revad)
<!--- [![committers.top badge](https://user-badge.committers.top/australia/007revad.svg)](https://user-badge.committers.top/australia/007revad) --->

### Description

Synology package to run iperf3 to test the network speed between devices and internet speed.
  - Test the speed between 2 local Synology NAS that both have this package installed.
  - Test internet speed from public internet iperf3 servers.

Available for DSM 7 and DSM 6.

**Note:** DSM 6 package only supports 86_64, armv8, armv7 and i686 (**not** x86, armv5, ppc or PowerPC)
  - For 13 series and older models [check your Synology model's CPU Arch here](https://kb.synology.com/en-global/DSM/tutorial/What_kind_of_CPU_does_my_NAS_have)

### How to install the package

There are 2 ways to install the package:

**Directly from Package Center**

1. Add [007revad Synology Package Source](https://github.com/007revad/Synology_package_source) to package Center.
2. Click on the Community section in Package Center and install the package.

<p align="center"><kbd><img src="/images/pkg_center.png"></kbd></p>

**Or download the package and install it manually**
1. Download the latest version .spk file from https://github.com/007revad/Synology_iperf3_Speedtest/releases and save it to your Synology.
2. In Package Center click on Manual Install.
3. Browse to where you downloaded the .spk file.
4. Select the .spk file and click Next.

### Screenshots

<!--- <p align="center">Description of image 1 goes here</p> --->
<p align="center"><kbd><img src="/images/installed.png"></kbd></p>

<br>

<p align="center">Select another local Synology or internet iperf3 server</p>
<p align="center"><kbd><img src="/images/window.png"></kbd></p>

<br>

<p align="center">Testing Synology to Synology speed</p>
<p align="center"><kbd><img src="/images/window2.png"></kbd></p>

<br>

<p align="center">Testing internet speed</p>
<p align="center"><kbd><img src="/images/window3.png"></kbd></p>

<br>

<p align="center">Copy the results</p>
<p align="center"><kbd><img src="/images/save_results.png"></kbd></p>

<br>

<p align="center">Settings</p>
<p align="center"><kbd><img src="/images/settings.png"></kbd></p>
