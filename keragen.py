from classes.sparser import *
from classes.quantizer import *
import sys, getopt
import math
import os, re

def main(argv):
    kerasfile=''
    trainvalid=''
    inputfile = None
    outputfile = None
    epochs=0
    batch_size=0
    verbose = False
    try:
        opts, args = getopt.getopt(argv,"hi:o:v", ["input=", "output="])
    except getopt.GetoptError:
        print('Usage : keragen.py -i <input.nn file> -o <output.py file>')
        exit(2)
    input_given = False
    for opt, arg in opts:
        if opt in ('-h', '--help'):
            print("""
Usage : keragen.py -i <input.nn file> -o <output.py file>

Mandatory options :
    -i <input.nn file>, --input <input.nn file>
                    Input .nn file name to be used for generation

Other options :
    -o <output.py file>, --output <output.py file>
                    Output .py file for generated Keras code

    -h, --help      Show this help message and exit
    
    -v, --verbose   Enable info messages during parsing of input .nn file""")
            exit()
        elif opt in ("-i", "--input"):
            inputfile = arg
            input_given = True
        elif opt in ("-o", "--output"):
            outputfile = arg
        elif opt in ("-v", "--verbose"):
            print("Running with verbose mode enabled.")
            verbose = True
    
    if not input_given:
        print("An input file has to be specified with the -i option. See help using -h for more info.")
        exit()
    
    sexpr = SParser(inputfile).parse(verbose=verbose)
    if str(sexpr.root) != "nnet-codegen":
        raise UserWarning("NN file should start with 'nnet-codegen'!")
    if verbose:
        sexpr.print()
    sexpr.validate(verbose)

    kerasfile+=build_header()

    print("Please enter batch size and number of epochs for training...")
    while batch_size < 1:
        try:
            batch_size = int(input("Batch size: "))
            if batch_size < 1:
                print("Please enter a valid positive integer.")
        except ValueError:
            print("Please enter a valid positive integer.")
            continue
    while epochs < 1:
        try:
            epochs = int(input("Number of epochs: "))
            if epochs < 1:
                print("Please enter a valid positive integer.")
        except ValueError:
            print("Please enter a valid positive integer.")
            continue
    
    kerasfile += define_training_variables(batch_size, epochs)

    while trainvalid.upper() not in ['Y', 'N']:
        trainvalid=input("Since this is a training program, weights and biases entered in the .nn file will be ignored.\n"+
        "Is that okay? [Y/N]")
        if trainvalid.upper() == 'N':
            exit()
        elif trainvalid.upper() != 'Y':
            print("Please make a valid choice [Y/N].")

    kerasfile += generate_layers(sexpr)
    kerasfile += create_training_loop()

    if outputfile is not None:
        kerasfile += enable_saving_weights_and_biases(outputfile)
        print("Writing Keras code to", outputfile)
        out = open(outputfile, 'w+')
        out.write(kerasfile)
        out.close()
        print
        run_now = ''
        while run_now.upper() not in ['Y', 'N']:
            run_now=input("Do you want to train the model right now [Y/N]?")
            if run_now.upper() == 'N':
                print("The Keras model can be launched and trained from the "+ outputfile + " file.")
                exit()
            elif run_now.upper() == 'Y':
                print("Training Keras model dynamically...")
                exec(kerasfile)
                quantize_now = ''
                while quantize_now.upper() not in ['Y', 'N']:
                    quantize_now=input("Do you want to quantize your weights and biases on a certain number of bits (experimental) [Y/N]?")
                    if quantize_now.upper() == 'N':
                        print("Weights and biases not quantized.")
                        exit()
                    elif quantize_now.upper() == 'Y':
                        print("How many bits do you want to quantize on (bits = int+frac parts)?")
                        bits = 0
                        while bits < 1:
                            try:
                                bits = int(input("Bits: "))
                                if bits < 1:
                                    print("Please enter a valid positive integer.")
                            except ValueError:
                                print("Please enter a valid positive integer.")
                                continue
                        qz = Quantizer()
                        for f in os.listdir('.'):
                            if f.startswith(outputfile.replace(".py", "") +"_b") or f.startswith(outputfile.replace(".py", "")+"_w"):
                                if verbose:
                                    print("Quantizing " + f + "... This may take a while.")
                                qz.quantize_file(bits, f)

            else:
                print("Please make a valid choice [Y/N].")
    else:
        print("No output file was defined. Training Keras model dynamically without saving weights or biases (use argument -o to write model to a file).")
        exec(kerasfile)
        exit()

    
    



def build_header():
    return """from __future__ import print_function
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K

"""

#ONLY MNIST SUPPORTED FOR NOW
def define_training_variables(batch_size, epochs):
    return """batch_size = """+str(batch_size)+"""
epochs = """+str(epochs)+"""
num_classes = 10

# input image dimensions
img_rows, img_cols = 28, 28

# the data, shuffled and split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

if K.image_data_format() == 'channels_first':
    x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
    x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
    input_shape = (1, img_rows, img_cols)
else:
    x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
    x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
    input_shape = (img_rows, img_cols, 1)

x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
print('x_train shape:', x_train.shape)
print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, num_classes)
y_test = keras.utils.to_categorical(y_test, num_classes)

model = Sequential()
"""

def generate_layers(sexpr):
    assert isinstance(sexpr, SNode)
    print("Generating...", sexpr.root)
    layers=""
    input_shape = tuple(map(int, filter(str.isdigit, map(str, sexpr.search("input").children))))
    all_layers = sexpr.search_all(["fc", "conv2d", "pool"])
    first_layer = True
    last_layer = ""
    for layer in all_layers:
        if str(layer.root) not in ["pool"]:
            output_size = int(str(layer.search("output").children[0]))
            activation_function = 'sigmoid' if layer.search("neuron").search("sigmoid") else 'relu'
        if str(layer.root) == "fc":
            if last_layer != "fc":
                if first_layer:
                    proxy_input = (int(math.sqrt(input_shape[0])), int(math.sqrt(input_shape[0])), 1)
                    layers+="""model.add(Flatten(input_shape="""+str(proxy_input)+"""))
"""
                    first_layer=False
                else:
                    layers+="""model.add(Flatten())
"""

            if first_layer:
                layers+="""model.add(Dense("""+str(output_size)+""", input_shape="""+str(input_shape)+""", activation='"""+activation_function+"""'))
"""
                first_layer=False
                print("Generated input FC layer with " + str(input_shape) + " inputs, " + str(output_size) + " neurons and a " + activation_function + " activation function.")
            else:
                layers+="""model.add(Dense("""+str(output_size)+""", activation='"""+activation_function+"""'))
"""
                print("Generated FC layer with " + str(output_size) + " neurons and a " + activation_function + " activation function.")

        if str(layer.root) == "conv2d":
            kernel_size = int(str(layer.search("kernel").children[0]))
            padding = str(layer.search("padding").children[0])
            stride = int(str(layer.search("stride").children[0]))
            if first_layer:
                layers+="""model.add(Conv2D("""+str(output_size)+""", padding='"""+padding+"""', kernel_size=("""+str(kernel_size)+""","""+str(kernel_size)+"""), strides=("""+str(stride)+""","""+str(stride)+"""), input_shape="""+str(input_shape)+""", activation='"""+activation_function+"""'))
"""
                first_layer=False
                print("Generated input Conv2D layer with " + str(input_shape) + " inputs, " + str(output_size) + " feature maps, '"+padding+"' padding, a kernel size of "+str(kernel_size)+", a stride of "+str(stride)+" and a " + activation_function + " activation function.")
            else:
                layers+="""model.add(Conv2D("""+str(output_size)+""", padding='"""+padding+"""', kernel_size=("""+str(kernel_size)+""","""+str(kernel_size)+"""), strides=("""+str(stride)+""","""+str(stride)+"""), activation='"""+activation_function+"""'))
"""
                print("Generated Conv2D layer with " + str(output_size) + " feature maps, '"+padding+"' padding, a kernel size of "+str(kernel_size)+", a stride of "+str(stride)+" and a " + activation_function + " activation function.")
        
        if str(layer.children[0].root) == "max":
            pool_size = int(str(layer.search("max").children[0]))
            padding = str(layer.search("padding").children[0])
            stride = int(str(layer.search("stride").children[0]))
            if first_layer:
                layers+="""model.add(MaxPooling2D(padding='"""+padding+"""', pool_size=("""+str(pool_size)+""","""+str(pool_size)+"""), strides=("""+str(stride)+""","""+str(stride)+"""), input_shape="""+str(input_shape)+"""))
"""
                first_layer=False
                print("Generated input MaxPooling2D layer with " + str(input_shape) + " inputs, a pool size of " + str(pool_size)+", '"+padding+"' padding and a stride of "+str(stride)+".")
            else:
                layers+="""model.add(MaxPooling2D(padding='"""+padding+"""', pool_size=("""+str(pool_size)+""","""+str(pool_size)+"""), strides=("""+str(stride)+""","""+str(stride)+""")))
"""
                print("Generated MaxPooling2D layer with a pool size of " + str(pool_size)+", '"+padding+"' padding and a stride of "+str(stride)+".")

        dropout = -1.0
        
        while dropout < 0.0 or dropout > 1.0:
            try:
                dropout = float(input("Dropout of this " + str(layer.root) + " layer for training [0.0-1.0]? Specify 0 for no dropout:"))
                if dropout < 0.0 or dropout > 1.0:
                    print("Please enter a dropout value in the range [0.0-1.0].")
            except ValueError:
                print("Please enter a valid real value (numbers).")
                continue
        
        if dropout == 0.0:
            print ("No dropout will be applied to this layer.")
        else:
            layers+="""model.add(Dropout("""+str(dropout)+"""))
"""
            print("Dropout of " + str(dropout) + " has been applied to this layer for training.")
        
        last_layer = str(layer.root)

    # TODO: Add prompt for softmax layer.
    if last_layer != "fc":
        layers+="""model.add(Flatten())
"""
    softmax = ''
    while softmax.upper()not in ['Y', 'N']:

        softmax = input("Add a softmax layer for classification purposes?")
        if softmax.upper() == 'N':
            print("Training without softmax classification layer.")
        elif softmax.upper() == 'Y':
            layers+="""model.add(Dense(num_classes, activation='softmax'))
"""
            print("Training with softmax classification layer.")


        

#Only supports MNIST for now
# TODO: Add functionality for other datasets.
    print("Done generating layers.")
    return layers

def create_training_loop():
    return """model.compile(loss=keras.losses.categorical_crossentropy, optimizer=keras.optimizers.Adadelta(), metrics=['accuracy'])

model.fit(x_train, y_train, batch_size=batch_size, epochs=epochs, verbose=1, validation_data=(x_test, y_test))

score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])
"""

def enable_saving_weights_and_biases(outputfile):
    filename = outputfile.replace(".py", "")
    savelines ="""
counter = 0
for layer in model.layers:
    if layer.get_weights():
        saver = open('"""+filename+"""_w'+str(counter)+'.nn', 'w+')
        saver.write(" ".join(map(str,layer.get_weights()[0].flatten().tolist())))
        saver.close()
        print('Saved weights for layer', str(counter))
        saver = open('"""+filename+"""_b'+str(counter)+'.nn', 'w+')
        saver.write(" ".join(map(str,layer.get_weights()[1].flatten().tolist())))
        saver.close()
        print('Saved biases for layer', str(counter))
        counter += 1

print('Weights and biases all saved.\\nThe last saved layer is a softmax layer; its weights can be ignored if not using softmax in the FPGA implementation.')
"""
# TODO: Add quantizer prompt and code.        
    return savelines


if __name__ == "__main__":
    main(sys.argv[1:])


