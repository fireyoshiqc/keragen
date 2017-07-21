# KeraGen
A Python library to be used with Keras in order to train hardware-implementable neural networks.

## Current features
* S-Expression parser that converts .nn files to a tree-like data structure.
* Support for hardware-compatible FC (fully-connected) layers.
* Support for hardware-compatible Conv2D and MaxPooling layers.
* Support for the MNIST dataset, provided by Keras.
* Support for sigmoid and ReLU hardware-compatible activation functions.
* Support for software (Keras) dropout and softmax layers.
* Parametrizable training parameters such as batch size and number of epochs.
* Complete Keras-enabled python file creation and saving.
* Dynamic execution of native Keras training routine from the keragen.py script.
* Saving of weights and biases in .nn files once the model is trained.
* Dynamic .nn file fixed-point precision handling (from saved weights and biases).
## Planned features
* Allow for more training parameters to be modified (optimizer, regularizers, etc.)
* Support for custom datasets.
* Handling more than one neural network per .nn file.
* Dynamic .nn file import handling (add saved weights and biases as imports).
* Implement as a real library, eventually a Python wheel.
