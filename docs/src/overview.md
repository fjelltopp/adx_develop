Technical Overview
===================

The AIDS Data Repository is a project conceptualised by the _UNAIDS Reference Group on Estimates, Modelling and Projections_. The project aims to improve the quality, accessibility and consistency of HIV data and HIV estimates by providing a centralised platform with tools to help countries manage and share their HIV data.

The initial phase of work was focussed on consulting with relevant stakeholders and putting a prototype solution in place that could be launched to a handful of countries. This work was put out to tender by UNAIDS on the UN Global Marketplace.  The tender was won by [Fjelltopp](fjelltopp.org) who collectively are initial authors of this documentation and code base.

In this Technical Overview we address broad concepts and structures that will be helpful in tracing the technical work that we have done. We hope that in time this documentation will grow to provide more detail concerning the project.

Principles of Prototyping
-------------------------

The prototype has been built with a view to:
 - *Demonstrating Potential* – We have focused on big-picture issues, not small user interface details.
 - *Ensuring Extendibility* – It is designed to be a good technical foundation upon which to continue building for years to come.
 - *Supporting Openess* – Entirely built from free open source solutions, with all new code made available through Github.
This explicitly means the project may not be well-tested, or well documented, or fully specced at this stage.


Component Technologies
----------------------

The AIDS Data Repository is built open an open source project called [CKAN](ckan.org).  This decision has determined most of the technology stack. Here we list technologies and frameworks adopted by the projects, and signpost to their corresponding documentation.

- Python
- Javascript
- Docker
- Linux
- CKAN
- AWS
- Travis
- Sphinx

Code Repositories
-----------------

Docker Infrastructure
---------------------

Cloud-Based Deployment
----------------------
