Plate Models
============

.. contents::
   :local:
   :depth: 1

This chapter describes all plate tectonic reconstruction models available in the
``plate-model-manager``. The models are listed in alphabetical order.
Aliases are noted where applicable.

Each model entry lists:

- **Time range** – the oldest (BigTime) and youngest (SmallTime) reconstruction time in Ma.
- **Layers** – the available data layers (e.g. Coastlines, Topologies).
- **Time-dependent rasters** – optional raster datasets that vary with time.
- **Description** – a brief description of the model.
- **DOI / URL** – a link to the original publication or data repository.

.. note::

   Use the model name (case-insensitive) when calling the ``plate-model-manager`` API or CLI.
   For example: ``pmm download Cao2024 ./my-models``

----

.. _model-alfonso2024:

alfonso2024
-----------

**Time range:** 0 – 170 Ma

**Layers:** Coastlines, ContinentalPolygons, COBs, Isochrons, StaticPolygons, Terranes, Topologies

**Time-dependent rasters:** AgeGrids, SpreadingRate

**Description:** alfonso2024

**DOI / URL:** https://doi.org/10.5281/zenodo.11392268

----

.. _model-cao2024:

cao2024
-------

**Aliases:** ``cao2023``

**Time range:** 0 – 18000 Ma

**Layers:** Coastlines, ContinentalPolygons, COBs, StaticPolygons, Topologies

**Description:** Earth's tectonic and plate boundary evolution over 1.8 billion years

**DOI / URL:** https://doi.org/10.5281/zenodo.11536686

----

.. _model-clennett2020-m2019:

clennett2020_m2019
------------------

**Aliases:** ``clennett2020``

**Time range:** 0 – 170 Ma

**Layers:** Coastlines, COBs, ContinentalPolygons, StaticPolygons, Terranes, Topologies

**Time-dependent rasters:** AgeGrids, SpreadingRate

**Description:** The model was implemented into the Müller et al. (2019) reference frame

**DOI / URL:** https://doi.org/10.5281/zenodo.10348270

----

.. _model-clennett2020-s2013:

clennett2020_s2013
------------------

**Time range:** 0 – 170 Ma

**Layers:** Coastlines, StaticPolygons, Terranes, Topologies

**Description:** The model was implemented into the Shephard et al. (2013) global plate model.

**DOI / URL:** https://doi.org/10.5281/zenodo.10348270

----

.. _model-domeier2014:

domeier2014
-----------

**Time range:** 250 – 410 Ma

**Layers:** Coastlines, StaticPolygons, Topologies

**Description:** unknown

----

.. _model-gibbons2015:

gibbons2015
-----------

**Time range:** 0 – 300 Ma

**Layers:** Coastlines, StaticPolygons, Topologies

**DOI / URL:** https://doi.org/10.5281/zenodo.10595658

----

.. _model-golonka:

golonka
-------

**Time range:** 0 – 540 Ma

**Layers:** Coastlines, StaticPolygons

**URL:** https://gwsdoc.gplates.org/models#golonka

----

.. _model-gurnis2012:

gurnis2012
----------

**Time range:** 0 – 140 Ma

**Layers:** Coastlines, StaticPolygons, Topologies

**Description:** Plate tectonic reconstructions with continuously closing plates

**DOI / URL:** https://doi.org/10.5281/zenodo.10596349

----

.. _model-matthews2016-mantle-ref:

matthews2016_mantle_ref
-----------------------

**Aliases:** ``matthews2016``

**Time range:** 0 – 410 Ma

**Layers:** Coastlines, ContinentalPolygons, StaticPolygons, Topologies

**Time-dependent rasters:** AgeGrids, Coastlines, Topologies

**Description:** This model is identical to MATTHEWS2016_pmag_ref in terms of relative plate models
but uses a true polar wander corrected paleomagnetic model, viewed as a proxy for a mantle reference
frame model.

**DOI / URL:** https://doi.org/10.5281/zenodo.10526156

----

.. _model-matthews2016-pmag-ref:

matthews2016_pmag_ref
---------------------

**Time range:** 0 – 410 Ma

**Layers:** Coastlines, ContinentalPolygons, StaticPolygons

**Description:** This plate model represents the first continuous late Paleozoic to present-day global
plate model with evolving plate boundaries, building on and extending two previously published models
for the late Paleozoic (410–250 Ma) (Domeier and Torsvik, 2014) and the MULLER2016 model
Mesozoic-Cenozoic (230–0 Ma). The model was designed for continuity during the 250–230 Ma transition
period between the two models, used an updated absolute reference frame of the Mesozoic-Cenozoic model
and added a new Paleozoic reconstruction for the Baltica-derived Alexander Terrane, now accreted to
western North America.

**URL:** https://gwsdoc.gplates.org/models#matthews2016_pmag_ref

----

.. _model-merdith2021:

merdith2021
-----------

**Time range:** 0 – 1000 Ma

**Layers:** Coastlines, ContinentalPolygons, Cratons, StaticPolygons, Topologies

**Description:** This plate model for the last 1000 Ma is based on a paleomagnetic reference frame.
In this model the longitudinal positions of the plates are unconstrained, due to the radial symmetry of
the Earth's magnetic field. It is broadly based on a modified combination of MULLER2016 for the last
230 Ma, the MATTHEWS2016_pmag_ref model for 250–410 Ma and a newly constructed model for earlier times.

**DOI / URL:** https://doi.org/10.5281/zenodo.10346399

----

.. _model-muller2008:

muller2008
----------

**Time range:** 0 – 140 Ma

**Layers:** StaticPolygons

----

.. _model-muller2016:

muller2016
----------

**Time range:** 0 – 230 Ma

**Layers:** Coastlines, COBs, StaticPolygons, Topologies

**Time-dependent rasters:** AgeGrids

**Description:** This model represents an update of the SETON2012 model, both in terms of relative and
absolute plate motions. The absolute reference used is based on the same hotspot model for the last
100 Ma as used in SETON2012, and a true-polar wander corrected paleomagnetic model for 230 to 100 Ma,
with an added 10 deg longitudinal correction for the time period from 100–230 Ma in an attempt to
minimise geodynamically unreasonable longitudinal plate motions, resulting in a modified mantle
reference frame.

**DOI / URL:** https://doi.org/10.5281/zenodo.10565444

----

.. _model-muller2019:

muller2019
----------

**Time range:** 0 – 250 Ma

**Layers:** Coastlines, COBs, ContinentalPolygons, Hotspots, Johansson2018LIPs, SeafloorFabric, StaticPolygons, Topologies, Whittaker2015LIPs

**Time-dependent rasters:** AgeGrids, SedimentThickness

**Description:** This plate model for the last 250 Ma is based on a mantle reference frame, ie it orients
the plates relative to the mantle using a set of geodynamic rules to exclude geodynamically unreasonable
plate motions, which typically result from models based on paleomagnetic data. The model also includes
continental deformation both along major rift systems and collisional plate boundary zones.

**DOI / URL:** https://doi.org/10.5281/zenodo.10525286

----

.. _model-muller2022:

muller2022
----------

**Time range:** 0 – 1000 Ma

**Layers:** Coastlines, COBs, ContinentalPolygons, Cratons, StaticPolygons, Topologies

**Time-dependent rasters:** AgeGrids, AgeGridsPMAG

**Description:** This model is based on MERDITH2021 for relative plate motions but uses a mantle
reference frame that orients the plates relative to the mantle using a set of geodynamic rules to
exclude geodynamically unreasonable plate motions. The difference between the paleomagnetic and mantle
reference frames grows cumulatively back in time – hence the two reconstructions (MERDITH2021 versus
MULLER2022) diverge progressively in the Paleozoic and Proterozoic both in terms of paleolatitude and
paleolongitude.

**DOI / URL:** https://doi.org/10.5281/zenodo.10297173

----

.. _model-paleomap:

paleomap
--------

**Aliases:** ``scotese2016``

**Time range:** 0 – 750 Ma

**Layers:** Coastlines, StaticPolygons

**Description:** also known as Scotese2016

**DOI / URL:** https://doi.org/10.5281/zenodo.10596609

----

.. _model-rodinia:

rodinia
-------

**Aliases:** ``li2008``

**Time range:** 530 – 1100 Ma

**Layers:** Coastlines, StaticPolygons

**URL:** https://gwsdoc.gplates.org/models#rodinia

----

.. _model-seton2012:

seton2012
---------

**Time range:** 0 – 200 Ma

**Layers:** Coastlines, COBs, ContinentalPolygons, StaticPolygons, Topologies

**Time-dependent rasters:** AgeGrids

**Description:** This model represents the first global plate model with topological plate boundaries.
It is based on a hybrid absolute reference frame, based on a moving hotspot model for the last 100 Ma,
and a true-polar wander corrected paleomagnetic model for 200 to 100 Ma. This combination of absolute
reference frames is viewed as a proxy for a mantle reference frame model.

**DOI / URL:** https://doi.org/10.5281/zenodo.10596049

----

.. _model-shephard2013:

shephard2013
------------

**Time range:** 0 – 200 Ma

**Layers:** Coastlines, StaticPolygons, Topologies

**Description:** the tectonic evolution of the Arctic since Pangea breakup

**DOI / URL:** https://doi.org/10.5281/zenodo.10595888

----

.. _model-shirmard2025:

shirmard2025
------------

**Aliases:** ``muller2025``

**Time range:** 0 – 18000 Ma

**Layers:** Coastlines, ContinentalPolygons, COBs, StaticPolygons, Topologies

**Time-dependent rasters:** AgeGrids, SpreadingRate

**Description:** How Subduction Evolution and Tectonic Stability Drive Sediment-Hosted Mineralization
Along Craton Edges.

**DOI / URL:** https://doi.org/10.5281/zenodo.15233548

----

.. _model-torsvikcocks2017:

torsvikcocks2017
----------------

**Time range:** 0 – 540 Ma

**Layers:** Coastlines, StaticPolygons

.. note::
   Only locations on land can be reconstructed with this model.

**URL:** https://www.earthdynamics.org/earthhistory/data_info.html

----

.. _model-young2018:

young2018
---------

**Time range:** 0 – 410 Ma

**Layers:** Coastlines, ContinentalPolygons, StaticPolygons, Topologies

**Description:** Global kinematics of tectonic plates and subduction zones since the late Paleozoic Era

**DOI / URL:** https://doi.org/10.5281/zenodo.10525369

----

.. _model-zahirovic2014:

zahirovic2014
-------------

**Time range:** 0 – 300 Ma

**Layers:** Coastlines, StaticPolygons

**DOI / URL:** https://doi.org/10.5281/zenodo.10595658

----

.. _model-zahirovic2016:

zahirovic2016
-------------

**Time range:** 0 – 230 Ma

**Layers:** Coastlines, ContinentalPolygons, Isochrons, StaticPolygons, Topologies

**Time-dependent rasters:** AgeGrids

**DOI / URL:** https://doi.org/10.5281/zenodo.10531296

----

.. _model-zahirovic2022:

zahirovic2022
-------------

.. note::
   This is the **default** plate model.

**Time range:** 0 – 410 Ma

**Layers:** Coastlines, ContinentalPolygons, StaticPolygons, Topologies

**Time-dependent rasters:** AgegridsUsingIsochronsMantleFrame, AgegridsUsingIsochronsPMAG, AgegridsUsingTopologiesMantleFrame, AgegridsUsingTopologiesPMAG, SpreadingRateUsingTopologiesMantleFrame, SpreadingRateUsingTopologiesPMAG

**Description:** Subduction kinematics and carbonate platform interactions

**DOI / URL:** https://doi.org/10.5281/zenodo.4729045
