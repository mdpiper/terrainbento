"""A template for making a derived ``terrainbento`` model.

This template shows all of the required parts of a new ``terrainbento`` model,
designed and created by **you**
"""

# import any major python libraries needed
# e.g. sys, os, numpy, scipy, pandas

# import all required parts of landlab
# e.g. landlab components you want to use

from terrainbento.base_class import ErosionModel


class ModelName(ErosionModel): # The model must inherit from either ErosionModel
                               # or StochasticErosionModel
    """ModelName is a template for making your own ``terrainbento`` models.

    This is where you will want to put introductory information about the model.

    """

    def __init__(self, input_file=None, params=None, BoundaryHandlers=None): # Do not change this line
    """
    Parameters
    ----------
    parameter_name : type
        This is an example parameter_name
    option_a : bool, optional
        List all parameters here, including their type, if they are optional,
        and what their default values are. Default value is True.

    Notes
    -----
    If there are other things you'd like users to know about, consider putting
    them here.

    Examples
    --------
    This is where you can make code examples showing how to use the model you
    created.

    >>> from terrainbento import ModelName
    >>> # this is where you'd show how to import and use your model.
    >>> # these statements get evaluated in testing so its also a way to show
    >>> # that the model does what you say it will do.
    >>> # its important to make sure that all lines of your model are tested
    >>> # either in these docstring tests or in test files.

    See also
    --------
    If there are references associated with your model, consider putting them
    here.

    """
    super(ModelName, self).__init__(input_file=input_file,                  # Replace  `ModelName` with your model name.
                                    params=params,                          # Do not change any additional parts of this
                                    BoundaryHandlers=BoundaryHandlers)      # line.

    # replace pass with all actions needed to initialize the model.
    pass

    def run_one_step(self, dt):
        """Run each component for one time step.

        Put any additional information about ``run_one_step`` here. Importantly,
        ``run_one_step`` should only take on parameter, ``dt``.
        """
        # replace pass with all actions needed to run the model forward for a time
        # increment `dt`.
        pass


    # if you have additional class functions, you can define them here.
    def my_internal_function(self):
        """Do something necessary to instantiate or run ``ModelName```."""
        # replace pass with function.
        pass

    # if your model has required finalization steps, define them here. This
    # definition will overwrite the empty `finalize` definition in the
    # `ErosionModel`.

    def finalize(self):
        """Finalize model.

        Put additional information about finalizing the model here.
        """
        # replace pass with all actions needed to finalize the model.
        pass


# this portion makes it possible to run the model from the command line.
def main():
    """Executes model."""
    import sys

    try:
        infile = sys.argv[1]
    except IndexError:
        print(('To run a terrainbento model from the command line you must '
                'include input file name on command line'))
        sys.exit(1)

    model = ModelName(input_file=infile)
    model.run()


if __name__ == '__main__':
    main()
