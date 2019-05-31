===================
Overview
===================


The purpose of Meerkat is to make data on public health surveillance available in a useful way to varied group of stakeholders. We use cased based data submitted from mobile devices, then the data is aggregated, and presented to the user via websites and reports. The system is currently implemented in Jordan with over 300 clinics reporting, and pilot project are implemented in Djibouti and Madagacar. 

All the data is submitted via ODK Collect to an ODK Aggregate Instance. From there the data is anonomised and passed on to the server running Meerkat. Meerkat consits of three different parts meerkat_abacus for importing and standardising data, meerkat_api gives an api for accesesing and aggregating data and meerkat_frontend which serves the data to the users. A demo of the system can be found at http://demo.emro.info (username: admin , password: secret).


