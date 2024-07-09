# coding: utf8
# !/usr/env/python
"""terrainbento model **BasicSaVs** program.

Erosion model using depth-dependent linear diffusion with a soil layer, basic
stream power, and discharge proportional to effective drainage area.

Landlab components used:
    1. `FlowAccumulator <https://landlab.readthedocs.io/en/master/reference/components/flow_accum.html>`_
    2. `DepressionFinderAndRouter <https://landlab.readthedocs.io/en/master/reference/components/flow_routing.html>`_ (optional)
    3. `FastscapeEroder <https://landlab.readthedocs.io/en/master/reference/components/stream_power.html>`_
    4. `DepthDependentDiffuser <https://landlab.readthedocs.io/en/master/reference/components/depth_dependent_diffusion.html>`_
    5. `ExponentialWeatherer <https://landlab.readthedocs.io/en/master/reference/components/weathering.html>`_
"""

import numpy as np
from landlab.components import (
    DepthDependentDiffuser,
    ExponentialWeatherer,
    FastscapeEroder,
)
from landlab.components.depression_finder.lake_mapper import _FLOODED

from terrainbento.base_class import ErosionModel


class BasicSaVs(ErosionModel):
    r"""**BasicSaVs** model program.

    This model program combines :py:class:`BasicSa` and :py:class:`BasicVs`.
    Given a spatially varying soil thickness :math:`H` and a spatially varying
    bedrock elevation :math:`\eta_b`, model **BasicSaVs** evolves a topographic
    surface described by :math:`\eta` with the following governing equations:

    .. math::

        \eta = \eta_b + H

        \frac{\partial H}{\partial t} = P_0 \exp (-H/H_s)
                                        - \delta (H) K A_{eff}^{M} S^{N}
                                        - \nabla q_h

        \frac{\partial \eta_b}{\partial t} = -P_0 \exp (-H/H_s)
                                       - (1 - \delta (H) ) K A_{eff}^{m} S^{N}

        q_h = -D H^* \left[1-\exp \left( -\frac{H}{H_0} \right) \right] \nabla \eta

        A_{eff} = A \exp \left( -\frac{-\alpha S}{A}\right)

        \alpha = \frac{K_{sat} H dx}{R_m}

    where :math:`Q` is the local stream discharge, :math:`S` is the local
    slope, :math:`m` and :math:`n` are the discharge and slope exponent
    parameters, :math:`K` is the erodibility by water, :math:`D` is the
    regolith transport parameter, :math:`H_s` is the sediment production decay
    depth, :math:`H_0` is the sediment transport decay depth, :math:`P_0` is
    the maximum sediment production rate, and :math:`H_0` is the sediment
    transport decay depth. :math:`q_h` is the hillslope sediment flux per unit
    width.

    :math:`\alpha` is the saturation area scale used for transforming area into
    effective area :math:`A_{eff}`. It is given as a function of the saturated
    hydraulic conductivity :math:`K_{sat}`, the soil thickness :math:`H`, the
    grid spacing :math:`dx`, and the recharge rate, :math:`R_m`.

    Refer to
    `Barnhart et al. (2019) <https://doi.org/10.5194/gmd-12-1267-2019>`_
    Table 5 for full list of parameter symbols, names, and dimensions.

    The following at-node fields must be specified in the grid:
        - ``topographic__elevation``
        - ``soil__depth``
    """

    _required_fields = ["topographic__elevation", "soil__depth"]

    def __init__(
        self,
        clock,
        grid,
        m_sp=0.5,
        n_sp=1.0,
        water_erodibility=0.0001,
        regolith_transport_parameter=0.1,
        soil_production__maximum_rate=0.001,
        soil_production__decay_depth=0.5,
        soil_transport_decay_depth=0.5,
        hydraulic_conductivity=0.1,
        **kwargs
    ):
        """
        Parameters
        ----------
        clock : terrainbento Clock instance
        grid : landlab model grid instance
            The grid must have all required fields.
        m_sp : float, optional
            Drainage area exponent (:math:`m`). Default is 0.5.
        n_sp : float, optional
            Slope exponent (:math:`n`). Default is 1.0.
        water_erodibility : float, optional
            Water erodibility (:math:`K`). Default is 0.0001.
        regolith_transport_parameter : float, optional
            Regolith transport efficiency (:math:`D`). Default is 0.1.
        soil_production__maximum_rate : float, optional
            Maximum rate of soil production (:math:`P_{0}`). Default is 0.001.
        soil_production__decay_depth : float, optional
            Decay depth for soil production (:math:`H_{s}`). Default is 0.5.
        soil_transport_decay_depth : float, optional
            Decay depth for soil transport (:math:`H_{0}`). Default is 0.5.
        hydraulic_conductivity : float, optional
            Hydraulic conductivity (:math:`K_{sat}`). Default is 0.1.
        **kwargs :
            Keyword arguments to pass to :py:class:`ErosionModel`. Importantly
            these arguments specify the precipitator and the runoff generator
            that control the generation of surface water discharge (:math:`Q`).

        Returns
        -------
        BasicSaVs : model object

        Examples
        --------
        This is a minimal example to demonstrate how to construct an instance
        of model **BasicSaVs**. For more detailed examples, including
        steady-state test examples, see the terrainbento tutorials.

        To begin, import the model class.

        >>> from landlab import RasterModelGrid
        >>> from landlab.values import random
        >>> from terrainbento import Clock, BasicSaVs
        >>> clock = Clock(start=0, stop=100, step=1)
        >>> grid = RasterModelGrid((5,5))
        >>> _ = random(grid, "topographic__elevation")
        >>> _ = random(grid, "soil__depth")

        Construct the model.

        >>> model = BasicSaVs(clock, grid)

        Running the model with ``model.run()`` would create output, so here we
        will just run it one step.

        >>> model.run_one_step(1.)
        >>> model.model_time
        1.0

        """
        # Call ErosionModel"s init
        super().__init__(clock, grid, **kwargs)

        # ensure Precipitator and RunoffGenerator are vanilla
        self._ensure_precip_runoff_are_vanilla(vsa_precip=True)

        # verify correct fields are present.
        self._verify_fields(self._required_fields)

        # Get Parameters and convert units if necessary:
        self.m = m_sp
        self.n = n_sp
        self.K = water_erodibility

        soil_thickness = self.grid.at_node["soil__depth"]
        bedrock_elev = self.grid.add_zeros("node", "bedrock__elevation")
        bedrock_elev[:] = self.z - soil_thickness

        # Get the effective-area parameter
        self._Kdx = hydraulic_conductivity * self.grid.dx

        # Instantiate a FastscapeEroder component
        self.eroder = FastscapeEroder(
            self.grid,
            discharge_field="surface_water__discharge",
            erode_flooded_nodes=self._erode_flooded_nodes,
            K_sp=self.K,
            m_sp=self.m,
            n_sp=self.n,
        )

        # Instantiate a ExponentialWeatherer and DepthDependentDiffuser component
        self.weatherer = ExponentialWeatherer(
            self.grid,
            soil_production_maximum_rate=soil_production__maximum_rate,
            soil_production_decay_depth=soil_production__decay_depth,
        )
        self.diffuser = DepthDependentDiffuser(
            self.grid,
            linear_diffusivity=regolith_transport_parameter,
            soil_transport_decay_depth=soil_transport_decay_depth,
        )

    def _calc_effective_drainage_area(self):
        """Calculate and store effective drainage area."""
        area = self.grid.at_node["drainage_area"]
        slope = self.grid.at_node["topographic__steepest_slope"]
        cores = self.grid.core_nodes

        sat_param = (
            self._Kdx
            * self.grid.at_node["soil__depth"]
            / self.grid.at_node["rainfall__flux"]
        )

        eff_area = area[cores] * (
            np.exp(-sat_param[cores] * slope[cores] / area[cores])
        )

        self.grid.at_node["surface_water__discharge"][cores] = eff_area

    def run_one_step(self, step):
        """Advance model **BasicVs** for one time-step of duration step.

        The **run_one_step** method does the following:

        1. Directs flow, accumulates drainage area, and calculates effective
           drainage area.

        2. Assesses the location, if any, of flooded nodes where erosion should
           not occur.

        3. Assesses if a :py:mod:`PrecipChanger` is an active boundary handler
           and if so, uses it to modify the erodibility by water.

        4. Calculates detachment-limited erosion by water.

        5. Calculates topographic change by linear diffusion.

        6. Finalizes the step using the :py:mod:`ErosionModel` base class
           function **finalize__run_one_step**. This function updates all
           boundary boundary handlers handlers by ``step`` and increments model time by
           ``step``.

        Parameters
        ----------
        step : float
            Increment of time for which the model is run.
        """
        # create and move water
        self.create_and_move_water(step)

        # Update effective runoff ratio
        self._calc_effective_drainage_area()

        # Zero out effective area in flooded nodes
        if self._erode_flooded_nodes:
            flooded_nodes = []
        else:
            flood_status = self.grid.at_node["flood_status_code"]
            flooded_nodes = np.nonzero(flood_status == _FLOODED)[0]

        self.grid.at_node["surface_water__discharge"][flooded_nodes] = 0.0

        # Do some erosion (but not on the flooded nodes)
        # (if we're varying K through time, update that first)
        if "PrecipChanger" in self.boundary_handlers:
            self.eroder.K = (
                self.K
                * self.boundary_handlers[
                    "PrecipChanger"
                ].get_erodibility_adjustment_factor()
            )
        self.eroder.run_one_step(step)

        # We must also now erode the bedrock where relevant. If water erosion
        # into bedrock has occurred, the bedrock elevation will be higher than
        # the actual elevation, so we simply re-set bedrock elevation to the
        # lower of itself or the current elevation.
        b = self.grid.at_node["bedrock__elevation"]
        b[:] = np.minimum(b, self.grid.at_node["topographic__elevation"])

        # Calculate regolith-production rate
        self.weatherer.calc_soil_prod_rate()

        # Do some soil creep
        self.diffuser.run_one_step(step)

        # Finalize the run_one_step_method
        self.finalize__run_one_step(step)


def main():  # pragma: no cover
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print("Must include input file name on command line")
        sys.exit(1)

    vssa = BasicSaVs.from_file(infile)
    vssa.run()


if __name__ == "__main__":
    main()
