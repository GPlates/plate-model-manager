Plate Models
============

.. contents::
   :local:
   :depth: 1

This chapter describes all plate tectonic reconstruction models available in the
``plate-model-manager``. 

Each model entry lists:

- **Time range** - begin time and end time of this model in Ma.
- **Layers** - the available data layers (e.g. Coastlines, Topologies).
- **Time-dependent rasters** - time-dependent raster files.
- **Description** - a brief description of the model.
- **DOI / URL** - a link to the original publication or data repository.

.. note::

   Use the model name (case-insensitive) when calling the ``plate-model-manager`` API or CLI.
   For example: ``pmm download Cao2024 ./my-models``

----

.. _model-default:

Default
-------

**Aliases:** :ref:`Zahirovic2022 <model-zahirovic2022>`

.. note::
   The current **default** plate model is :ref:`Zahirovic2022 <model-zahirovic2022>`. This may change in the future as new models are added or updated. Always check the documentation for the most up-to-date information on the default model.

----

.. _model-muller2025:

Muller2025
----------

**Aliases:** :ref:`Shirmard2025 <model-shirmard2025>`

**Time range:** 18000 - 0 Ma

**Layers:**

- Coastlines 
- ContinentalPolygons
- COBs 
- StaticPolygons
- Topologies

**Time-dependent rasters:**

- AgeGrids
- SpreadingRate

**Description:** Mantle-reference plate model based on Cao et al. (2024), covering deep-time reconstructions. See the
'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.15233548

----

.. _model-shirmard2025:

Shirmard2025
------------

**Aliases:** :ref:`Muller2025 <model-muller2025>`

**Time range:** 18000 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- COBs
- StaticPolygons
- Topologies


**Time-dependent rasters:**

- AgeGrids
- SpreadingRate


**Description:** Mantle-reference plate model based on Cao et al. (2024), covering deep-time reconstructions. See the
'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.15233548

----

.. _model-alfonso2024:

Alfonso2024
-----------

**Time range:** 170 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- COBs
- Isochrons
- StaticPolygons
- Terranes
- Topologies


**Time-dependent rasters:**

- AgeGrids
- SpreadingRate


**Description:** Modified global model focused on Western North America and the eastern Pacific tomotectonic
reconstruction. Set the anchor plate ID to 701701 to use PMAG reference frame. See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.11392268

----

.. _model-cao2024:

Cao2024
-------

**Aliases:** Cao2023

**Time range:** 18000 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- COBs
- StaticPolygons
- Topologies


**Description:** Global tectonic and plate-boundary reconstruction spanning ~1.8 billion years. See the 'URL' below
for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.11536686

----

.. _model-cao2023:

Cao2023
-------

**Aliases:** :ref:`Cao2024 <model-cao2024>`

----

.. _model-muller2022:

Muller2022
----------

**Time range:** 1000 - 0 Ma

**Layers:**

- Coastlines
- COBs
- ContinentalPolygons
- Cratons
- StaticPolygons
- Topologies


**Time-dependent rasters:**

- AgeGrids
- AgeGridsPMAG


**Description:** This model is based on MERDITH2021 for relative plate motions but uses a mantle reference frame that
orients the plates relative to the mantle using a set of geodynamic rules to exclude geodynamically
unreasonable plate motions. The difference between the paleomagnetic and mantle reference frames
grows cumulatively back in time - hence the two reconstructions (MERDITH2021 versus MULLER2022)
diverge progressively in the Paleozoic and Proterozoic both in terms of paleolatitude and
paleolongitude. See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10297173

----

.. _model-zahirovic2022:

Zahirovic2022
-------------

.. note::
   This is the **default** plate model.

**Time range:** 410 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- StaticPolygons
- Topologies

**Time-dependent rasters:**

- AgegridsUsingIsochronsMantleFrame
- AgegridsUsingIsochronsPMAG
- AgegridsUsingTopologiesMantleFrame
- AgegridsUsingTopologiesPMAG
- SpreadingRateUsingTopologiesMantleFrame
- SpreadingRateUsingTopologiesPMAG


**Description:** Model for subduction kinematics and carbonate platform interactions. Set the anchor plate ID to 701701 to use PMAG reference frame. See the 'URL' below for more
details.

**DOI / URL:** https://doi.org/10.5281/zenodo.4729045

----

.. _model-merdith2021:

Merdith2021
-----------

**Time range:** 1000 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- Cratons
- StaticPolygons
- Topologies


**Description:** This plate model for the last 1000 Ma is based on a paleomagnetic reference frame. In this model the
longitudinal positions of the plates are unconstrained, due to the radial symmetry of the Earth's
magnetic field. It is broadly based on a modified combination of MULLER2016 for the last 230 Ma, the
MATTHEWS2016_pmag_ref model for 250-410 Ma and a newly constructed model for earlier times. See the
'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10346399

----

.. _model-clennett2020:

Clennett2020
------------

**Aliases:** :ref:`Clennett2020_m2019 <model-clennett2020-m2019>`

**Time range:** 170 - 0 Ma

**Layers:**

- Coastlines
- COBs
- ContinentalPolygons
- StaticPolygons
- Terranes
- Topologies


**Time-dependent rasters:**

- AgeGrids
- SpreadingRate


**Description:** Quantitative tomotectonic reconstruction of western North America and the eastern Pacific basin. See
the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10348270

----

.. _model-clennett2020-m2019:

Clennett2020_m2019
------------------

**Aliases:** :ref:`Clennett2020 <model-clennett2020>`

**Time range:** 170 - 0 Ma

**Layers:**

- Coastlines
- COBs
- ContinentalPolygons
- StaticPolygons
- Terranes
- Topologies


**Time-dependent rasters:**

- AgeGrids
- SpreadingRate


**Description:** Quantitative tomotectonic reconstruction of western North America and the eastern Pacific basin. See
the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10348270

----

.. _model-clennett2020-s2013:

Clennett2020_s2013
------------------

**Time range:** 170 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons
- Terranes
- Topologies


**Description:** Quantitative tomotectonic reconstruction of western North America and the eastern Pacific basin. See
the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10348270

----

.. _model-muller2019:

Muller2019
----------

**Time range:** 250 - 0 Ma

**Layers:**

- Coastlines
- COBs
- ContinentalPolygons
- Hotspots
- Johansson2018LIPs
- SeafloorFabric
- StaticPolygons
- Topologies
- Whittaker2015LIPs


**Time-dependent rasters:**

- AgeGrids
- SedimentThickness


**Description:** This plate model for the last 250 Ma is based on a mantle reference frame, ie it orients the plates
relative to the mantle using a set of geodynamic rules to exclude geodynamically unreasonable plate
motions, which typically result from models based on paleomagnetic data. The model also includes
continental deformation both along major rift systems and collisional plate boundary zones. See the
'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10525286

----

.. _model-young2018:

Young2018
---------

**Time range:** 410 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- StaticPolygons
- Topologies


**Description:** Global plate and subduction-zone kinematics since the late Paleozoic. See the 'URL' below for more
details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10525369

----

.. _model-torsvikcocks2017:

Torsvikcocks2017
----------------

**Time range:** 540 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons


.. note::
   Only locations on land can be reconstructed with this model.

**Description:** Earth History and Palaeogeography reconstruction resource (Torsvik and Cocks framework). See the
'URL' below for more details.

**URL:** https://www.earthdynamics.org/earthhistory/data_info.html

----

.. _model-matthews2016:

Matthews2016
------------

**Aliases:** :ref:`Matthews2016_mantle_ref <model-matthews2016-mantle-ref>`

**Time range:** 410 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- StaticPolygons
- Topologies


**Time-dependent rasters:**

- AgeGrids
- Coastlines
- Topologies


**Description:** This model is identical to MATTHEWS2016_pmag_ref in terms of relative plate models but uses a true
polar wander corrected paleomagnetic model, viewed as a proxy for a mantle reference frame model. See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10526156

----

.. _model-matthews2016-mantle-ref:

Matthews2016_mantle_ref
-----------------------

**Aliases:** :ref:`Matthews2016 <model-matthews2016>`

**Time range:** 410 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- StaticPolygons
- Topologies


**Time-dependent rasters:**

- AgeGrids
- Coastlines
- Topologies


**Description:** This model is identical to MATTHEWS2016_pmag_ref in terms of relative plate models but uses a true
polar wander corrected paleomagnetic model, viewed as a proxy for a mantle reference frame model. See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10526156

----

.. _model-matthews2016-pmag-ref:

Matthews2016_pmag_ref
---------------------

**Time range:** 410 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- StaticPolygons


**Description:** This plate model represents the first continuous late Paleozoic to present-day global plate model
with evolving plate boundaries, building on and extending two previously published models for the
late Paleozoic (410-250 Ma) (Domeier and Torsvik, 2014) and the MULLER2016 model Mesozoic-Cenozoic
(230-0 Ma). The model was designed for continuity during the 250-230 Ma transition period between
the two models, used an updated absolute reference frame of the Mesozoic-Cenozoic model and added a
new Paleozoic reconstruction for the Baltica-derived Alexander Terrane, now accreted to western
North America. See the 'URL' below for more details.

**URL:** https://gwsdoc.gplates.org/models#matthews2016_pmag_ref

----

.. _model-muller2016:

Muller2016
----------

**Time range:** 230 - 0 Ma

**Layers:**

- Coastlines
- COBs
- StaticPolygons
- Topologies


**Time-dependent rasters:**

- AgeGrids


**Description:** This model represents an update of the SETON2012 model, both in terms of relative and absolute plate
motions. The absolute reference used is based on the same hotspot model for the last 100 Ma as used
in SETON2012, and a true-polar wander corrected paleomagnetic model for 230 to 100 Ma, with an added
10 deg longitudinal correction for the time period from 100-230 Ma in an attempt to minimise
geodynamically unreasonable longitudinal plate motions, resulting in a modified mantle reference
frame. See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10565444

----

.. _model-scotese2016:

Scotese2016
-----------

**Aliases:** :ref:`Paleomap <model-paleomap>`

**Time range:** 750 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons


**Description:** PALEOMAP PaleoAtlas reconstruction dataset for GPlates (Scotese framework). See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10596609

----

.. _model-zahirovic2016:

Zahirovic2016
-------------

**Time range:** 230 - 0 Ma

**Layers:**

- Coastlines
- ContinentalPolygons
- Isochrons
- StaticPolygons
- Topologies


**Time-dependent rasters:**

- AgeGrids


**Description:** Eastern Tethys tectonic evolution and deep-mantle-structure reconstruction since the latest
Jurassic. See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10531296

----

.. _model-gibbons2015:

Gibbons2015
-----------

**Time range:** 300 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons
- Topologies


**Description:** Model reconciling India-Eurasia and intra-oceanic arc collisions in the central-eastern Tethys. See
the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10595658

----

.. _model-domeier2014:

Domeier2014
-----------

**Time range:** 410 - 250 Ma

**Layers:**

- Coastlines
- StaticPolygons
- Topologies


**Description:** unknown

----

.. _model-zahirovic2014:

Zahirovic2014
-------------

**Time range:** 300 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons


**Description:** Model reconciling India-Eurasia and intra-oceanic arc collisions in the central-eastern Tethys. See
the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10595658

----

.. _model-shephard2013:

Shephard2013
------------

**Time range:** 200 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons
- Topologies


**Description:** Arctic tectonic evolution model since Pangea breakup integrating geology, geophysics, and mantle
context. See the 'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10595888

----

.. _model-gurnis2012:

Gurnis2012
----------

**Time range:** 140 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons
- Topologies


**Description:** Continuously closing-plate reconstruction model for self-consistent global plate polygons. See the
'URL' below for more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10596349

----

.. _model-seton2012:

Seton2012
---------

**Time range:** 200 - 0 Ma

**Layers:**

- Coastlines
- COBs
- ContinentalPolygons
- StaticPolygons
- Topologies


**Time-dependent rasters:**

- AgeGrids


**Description:** This model represents the first global plate model with topological plate boundaries. It is based on
a hybrid absolute reference frame, based on a moving hotspot model for the last 100 Ma, and a true-
polar wander corrected paleomagnetic model for 200 to 100 Ma. This combination of absolute reference
frames is viewed as a proxy for a mantle reference frame model. See the 'URL' below for more
details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10596049

----

.. _model-li2008:

**Aliases:** :ref:`Rodinia <model-rodinia>`

----

.. _model-muller2008:

Muller2008
----------

**Time range:** 140 - 0 Ma

**Layers:**

- StaticPolygons


**Description:** MULLER2008 model data archive.

**URL:** https://earthbyte.org/webdav/ftp/incoming/mchin/plate-models/MULLER2008,

----

.. _model-golonka:

Golonka
-------

**Time range:** 540 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons


**Description:** Community-driven paleogeographic reconstruction model (GOLONKA) with deep-time coverage. See the
'URL' below for more details.

**URL:** https://gwsdoc.gplates.org/models#golonka

----

.. _model-paleomap:

Paleomap
--------

**Aliases:** :ref:`Scotese2016 <model-scotese2016>`

**Time range:** 750 - 0 Ma

**Layers:**

- Coastlines
- StaticPolygons


**Description:** PALEOMAP PaleoAtlas reconstruction dataset for GPlates (Scotese framework). See the 'URL' below for
more details.

**DOI / URL:** https://doi.org/10.5281/zenodo.10596609


----

.. _model-rodinia:

Rodinia
-------

**Aliases:** Li2008

**Time range:** 1100 - 530 Ma

**Layers:**

- Coastlines
- StaticPolygons


**Description:** Rodinia-focused Precambrian reconstruction model for deep-time paleogeography. See the 'URL' below
for more details.

**URL:** https://gwsdoc.gplates.org/models#rodinia
