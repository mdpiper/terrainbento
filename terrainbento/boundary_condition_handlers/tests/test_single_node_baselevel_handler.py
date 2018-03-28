import sys
import os

import numpy as np

from numpy.testing import assert_almost_equal
from nose.tools import assert_raises

from terrainbento.boundary_condition_handlers import SingleNodeBaselevelHandler
from landlab import RasterModelGrid, HexModelGrid

_TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

def text_hex():
    "Test using a hex grid"

    mg = HexModelGrid(5, 5)
    z = mg.add_zeros('node', 'topographic__elevation')

    bh = SingleNodeBaselevelHandler(mg, outlet_node = 0, outlet_lowering_rate = 0.1)
    bh.run_one_step(10.0)

    assert z[0] == -1.0


def test_passing_neither_lowering_method():
    """Test passing no lowering information"""
    mg = RasterModelGrid(5, 5)
    z = mg.add_zeros('node', 'topographic__elevation')

    assert_raises(ValueError,
                  SingleNodeBaselevelHandler,
                  mg, outlet_node=0)


def test_passing_both_lowering_methods():
    """Test passing both lowering methods"""
    mg = RasterModelGrid(5, 5)
    z = mg.add_zeros('node', 'topographic__elevation')
    file = os.path.join(_TEST_DATA_DIR, 'outlet_history.txt')

    assert_raises(ValueError,
                  SingleNodeBaselevelHandler,
                  mg, outlet_node=0,
                  outlet_lowering_rate = 0.1,
                  outlet_lowering_file_path=file)

def test_outlet_lowering_object_bad_file():
    """Test using an outlet lowering object with a bad file"""

    mg = HexModelGrid(5, 5)
    z = mg.add_zeros('node', 'topographic__elevation')

    assert_raises(ValueError,
                  SingleNodeBaselevelHandler,
                  mg,
                  outlet_node = 0,
                  outlet_lowering_file_path='foo.txt')

def test_outlet_lowering_rate_no_scaling_bedrock():
    """Test using an outlet lowering object with no scaling and bedrock"""

    mg = HexModelGrid(5, 5)
    z = mg.add_ones('node', 'topographic__elevation')
    b = mg.add_zeros('node', 'bedrock__elevation')

    node_id = 27
    bh = SingleNodeBaselevelHandler(mg,
                                    outlet_node = node_id,
                                    outlet_lowering_rate = 0.1)
    bh.run_one_step(2400.0)

    assert z[node_id] == -239.0
    assert b[node_id] == -240.0

def test_outlet_lowering_object_no_scaling_bedrock():
    """Test using an outlet lowering object with no scaling and bedrock"""

    mg = HexModelGrid(5, 5)
    z = mg.add_ones('node', 'topographic__elevation')
    b = mg.add_zeros('node', 'bedrock__elevation')

    node_id = 27
    file = os.path.join(_TEST_DATA_DIR, 'outlet_history.txt')
    bh = SingleNodeBaselevelHandler(mg,
                                    outlet_node = node_id,
                                    outlet_lowering_file_path=file)
    bh.run_one_step(2400.0)

    assert z[node_id] == -46.5
    assert b[node_id] == -47.5

def test_outlet_lowering_object_no_scaling():
    """Test using an outlet lowering object with no scaling"""

    mg = HexModelGrid(5, 5)
    z = mg.add_zeros('node', 'topographic__elevation')
    node_id = 27
    file = os.path.join(_TEST_DATA_DIR, 'outlet_history.txt')
    bh = SingleNodeBaselevelHandler(mg,
                                    outlet_node = node_id,
                                    outlet_lowering_file_path=file)
    bh.run_one_step(2400.0)

    assert bh.z[node_id] == -47.5


def test_outlet_lowering_object_with_scaling():
    """Test using an outlet lowering object with scaling"""

    mg = HexModelGrid(5, 5)
    z = mg.add_zeros('node', 'topographic__elevation')
    node_id = 27
    file = os.path.join(_TEST_DATA_DIR, 'outlet_history.txt')
    bh = SingleNodeBaselevelHandler(mg,
                                    outlet_node = node_id,
                                    outlet_lowering_file_path=file,
                                    model_end_elevation = -318.0)
    bh.run_one_step(2400.0)
    assert bh.z[node_id] == -95.0
