from datetime import datetime
import math
import matplotlib.pyplot as plt
import numpy as np


# Utils
def print_current_results(epochs, Model, train_features, train_target,
                          test_features, test_target, loss_sum, prefix=""):
    train_error = compute_accuracy(Model, train_features, train_target)
    test_error = compute_accuracy(Model, test_features, test_target)
    print(prefix + "Epoch: {}, Train Error: {:.4f}%,\
        Test Error: {:.4f}%, Loss  {:.4f}".format(epochs, train_error,
                                                  test_error, loss_sum))


def print_in_color(message, color="red"):
    choices = {"green": "32", "blue": "34",
               "magenta": "35", "red": "31",
               "Gray": "37", "Cyan": "36"}
    if message == "-h":
        return list(choices.keys())
    elif color == "":
        print(message)
    elif color in choices:
        print("\033[" + choices[color] + "m" + message + "\033[0m")
    else:
        raise ValueError("Available colors: {}, '-h' to get\
            the list".format(choices.keys()))


def train_homemade_model(model, num_epochs, train_features,
                         train_target, test_features,
                         test_target, batch_size):
    start_time = datetime.now()
    # Convert train_target to one hot encoding
    train_target_one_hot = convert_to_one_hot_labels(train_features,
                                                     train_target)

    print_current_results(0, model, train_features, train_target,
                          test_features, test_target, 0,
                          prefix="Before training: ")
    test_results = []
    for epochs in range(0, num_epochs):
        loss_sum = 0
        test_results.append(get_inferences(model, test_features))
        for b in range(train_features.shape[0] // batch_size):
            output = model.forward(train_features[
                list(range(b*batch_size, (b+1)*batch_size))])
            loss = model.backward(train_target_one_hot[
                list(range(b*batch_size, (b+1)*batch_size))],
                                  output)
            loss_sum = loss_sum + loss.item()
        if epochs % 30 == 0:
            print_current_results(epochs + 1, model, train_features,
                                  train_target, test_features,
                                  test_target, loss_sum)

    training_time = datetime.now() - start_time
    print('\nTraining time: {}'.format(training_time))
    print_current_results(epochs, model, train_features, train_target,
                          test_features, test_target, loss_sum,
                          prefix="After training: ")


# Data Manager
def generate_disc_set(nb):
    features = np.random.uniform(-1, 1, (nb, 2))
    target = (features[:, 0]**2 + features[:, 1]**2)/math.pi < 0.2
    return features, target.astype(int)


def plot_dataset(features, target):
    fig, ax = plt.subplots(figsize=(4, 4))
    plt.title("Dataset")
    scatter = ax.scatter(features[:, 0], features[:, 1],
                         c=target)
    legend = ax.legend(*scatter.legend_elements(), title="Labels",
                       loc="lower right")
    ax.add_artist(legend)
    return plt


def convert_to_one_hot_labels(features, target):
    n_values = max(target) + 1
    target_onehot = np.eye(n_values)[target]
    return target_onehot


def compute_accuracy(model, data_features, data_target):
    predicted_classes = get_inferences(model, data_features)
    nb_data_errors = sum(data_target != predicted_classes)
    return nb_data_errors/data_features.shape[0]*100


def get_inferences(model, data_features):
    output = model.forward(data_features)
    predicted_classes = np.argmax(output, axis=1)
    return predicted_classes


# Classes
possible_types = ["Linear", "Activation", "Loss",
                  "Softmax", "Flatten", "Convolution"]


# heritage module definition
class Module(object):
    def __init__(self):
        super().__init__()
        self.lr = 0

    def forward(self, *input):
        raise NotImplementedError

    def backward(self, *gradwrtoutput):
        raise NotImplementedError


# RelU activation function
class ReLU(Module):
    def __init__(self):
        super().__init__()
        self.type = "Activation"
        self.save = 0

    def forward(self, x):
        self.save = x
        x[x < 0] = 0
        y = x
        return y

    def backward(self, x):
        y = (self.save > 0).astype(float)
        return np.multiply(y, x)

    def print(self, color=""):
        print_in_color("\tReLU activation", color)
        return


# LeakyReLU activation function
class LeakyReLU(Module):
    def __init__(self):
        super().__init__()
        self.type = "Activation"
        self.save = 0
        self.a = 0.01

    def forward(self, x):
        self.save = x
        neg = x < 0
        pos = x >= 0
        y = np.multiply(neg.astype(float), x)*self.a +\
            np.multiply(pos.astype(float), x)
        return y

    def backward(self, x):
        neg = self.save < 0
        pos = self.save >= 0
        y = np.multiply(neg.astype(float), x)*self.a +\
            np.multiply(pos.astype(float), x)
        return y

    def print(self, color=""):
        print_in_color("\tLeakyReLU activation", color)
        return


# sigmoid activation function
class Sigmoid(Module):
    def __init__(self):
        super().__init__()
        self.type = "Activation"
        self.save = 0

    def eq(self, x):
        return 1 / (1 + np.exp(np.multiply(x, -1)))

    def forward(self, x):
        self.save = x
        y = self.eq(x)
        return y

    def backward(self, x):
        y = np.multiply(self.eq(self.save) * (1 - self.eq(self.save)), x)
        return y

    def print(self, color=""):
        print_in_color("\tSigmoid activation", color)
        return


# MSE Loss implementation
class LossMSE(Module):
    def __init__(self):
        super().__init__()
        self.type = "Loss"

    def loss(self, y, y_pred):
        loss = sum(((y_pred - y)**2).sum(axis=0))/y.shape[1]
        return loss

    def print(self, color=""):
        print_in_color("\tMSE", color)

    def grad(self, y, y_pred):
        return 2*(y_pred-y)/y.shape[1]


# Softmax function implementation
class Softmax(Module):
    def __init__(self):
        super().__init__()
        self.type = "Softmax"
        self.save = 0

    def eq(self, x):
        return np.exp(x)/np.sum(np.exp(x), axis=1)[:, None]

    def forward(self, x):
        self.save = x
        y = self.eq(x)
        return y

    def backward(self, x):
        y = np.multiply(self.eq(self.save) * (1 - self.eq(self.save)), x)
        return y

    def print(self, color=""):
        print_in_color("\tSoftmax function", color)
        return


# Softmax function implementation
class Batch_Norm(Module):
    def __init__(self, batch_size):
        super().__init__()
        self.type = "Batch Normalization"
        self.gamma = 1
        self.eps = 10**-100
        self.beta = 0
        self.x_mu = 0
        self.inv_var = 0
        self.x_hat = 0

    def eq(self, x):
        return np.exp(x)/np.sum(np.exp(x), axis=1)[:, None]

    def forward(self, x):
        self.save = x
        mean = np.sum(x, axis=1)/x.shape[1]
        mean_repeated = np.repeat(mean[:, None], x.shape[1], axis=1)
        self.x_mu = x - mean_repeated
        var = np.sum((x-mean_repeated)**2, axis=1)/x.shape[1]
        var_repeated = np.repeat(var[:, None], x.shape[1], axis=1)
        self.inv_var = 1/(np.sqrt(var_repeated) + self.eps)
        self.x_hat = self.x_mu * self.inv_var
        norm = (x - mean_repeated)/(np.sqrt(var_repeated) + self.eps)
        return norm*self.gamma + self.beta

    def backward(self, x):
        N, D = x.shape
        dxhat = x * self.gamma
        dx = (1. / N) * self.inv_var * (N*dxhat - np.sum(dxhat, axis=0)
                                        - self.x_hat*np.sum(
                                            dxhat*self.x_hat, axis=0))
        dbeta = np.sum(np.sum(x, axis=1))
        dgamma = np.sum(np.sum(self.x_hat*x, axis=1))
        # todo fix gamma update
        # self.gamma = self.gamma - dgamma
        # self.beta = self.beta - dbeta
        return dx

    def print(self, color=""):
        print_in_color("\tBatch normalization function", color)
        return


# Linear layer
class Linear(Module):
    def __init__(self, in_features, out_features):
        super().__init__()
        self.type = "Linear"
        self.x = np.zeros(out_features)
        self.in_features = in_features
        self.out_features = out_features
        stdv = 1. / math.sqrt(self.out_features)
        self.weight = np.random.uniform(-stdv, stdv, (self.in_features,
                                                      self.out_features))
        self.bias = np.random.uniform(-stdv, stdv, (self.out_features, 1))

    def print(self, color=""):
        msg = "\tLinear layer shape: {}".format([self.weight.shape[0],
                                                 self.weight.shape[1]])
        print_in_color(msg, color)

    def print_weight(self):
        print(self.weight)

    def update(self, grad):
        lr = self.lr
        self.weight = self.weight -\
            np.multiply(lr, np.matmul(np.transpose(self.x), grad))
        self.bias = self.bias -\
            lr*grad.mean(0).reshape([self.bias.shape[0], 1])*1

    def backward(self, grad):
        b = np.matmul(grad, np.transpose(self.weight))
        self.update(grad)
        return b

    def forward(self, x):
        self.x = x
        return np.matmul(x, self.weight) +\
            np.transpose(np.repeat(self.bias, x.shape[0], axis=1))

    def set_Lr(self, lr):
        self.lr = lr
        return


# Convolutional layer
class Convolution(Module):
    def __init__(self, in_channels=1, out_channels=16,
                 kernel_size=3, stride=1, padding=1):
        super().__init__()
        self.type = "Convolution"
        self.k_height = kernel_size
        self.k_width = kernel_size
        self.x_width = 0
        self.x_height = 0
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.stride = stride
        self.padding = padding
        stdv = 1. / math.sqrt(self.k_height)
        self.kernel = np.random.uniform(-stdv, stdv, (self.out_channels,
                                                      self.in_channels,
                                                      self.k_height,
                                                      self.x_width))

    def print(self, color=""):
        msg = "\tConvolution feature maps: {}, kernel size: {}".format(
            self.out_channels, self.kernel.shape)
        print_in_color(msg, color)

    def print_kernels(self):
        print(self.kernel)

    def set_Lr(self, lr):
        self.lr = lr
        return

    def update(self, grad):
        lr = self.lr
        self.weight = self.weight
        self.bias = self.bias

    def forward(self, x):
        self.x = x
        self.x_width = x.shape[1]
        self.x_height = x.shape[2]

        patches = np.asarray([x[c, self.stride*j:self.stride*j+self.k_height,
                                self.stride*k:self.stride*k+self.k_width]
                              for c in range(self.in_channels)
                              for j in range(self.x_height-self.k_height+1)
                              for k in range(self.x_width-self.k_width+1)])
        patches = patches.reshape([self.in_channels, math.ceil(
            patches.shape[0]/self.in_channels),
                                   self.k_height*self.k_width])
        # print("patches shape", patches.shape)
        kernel_repeat = np.repeat(kernel.reshape([self.out_channels,
                                                  self.in_channels, 1,
                                                  self.k_height*self.k_width]),
                                  patches.shape[1], axis=2)
        # print("kernel_repeat shape", kernel_repeat.shape)
        result = np.asarray([np.matmul(kernel_repeat[o, c, j, :],
                                       patches[c, j, :])
                             for o in range(out_channels)
                             for c in range(patches.shape[0])
                             for j in range(patches.shape[1])])
        # print("result shape", result.shape)
        result = result.reshape([kernel_repeat.shape[0],
                                 kernel_repeat.shape[1],
                                 self.x_height-self.k_height+1,
                                 self.x_width-self.k_width+1])
        y = np.sum(result, axis=1)
        # print("y shape", y.shape)
        return y

    def backward(self, grad):
        return grad

    def set_Lr(self, lr):
        self.lr = lr
        return


# Flatten function implementation
class Flatten(Module):
    def __init__(self):
        super().__init__()
        self.type = "Flatten"

    def forward(self, x):
        y = x.reshape([np.prod(x.shape)])
        return y

    def backward(self, x):
        return x

    def print(self, color=""):
        print_in_color("\tFlatten function", color)
        return


# Sequential architecture
class Sequential(Module):
    def __init__(self, param, loss):
        super().__init__()
        self.type = "Sequential"
        self.model = param
        self.loss = loss

    def forward(self, x):
        for _object in self.model:
            x = _object.forward(x)
        return x

    def backward(self, y, y_pred):
        loss = self.loss.loss(y, y_pred)
        grad_pred = self.loss.grad(y, y_pred)
        for _object in reversed(self.model):
            grad_pred = _object.backward(grad_pred)
        return loss

    def print(self, print_color=True):
        possible_colors = print_in_color("-h")
        if len(possible_colors) < len(possible_types):
            print('Not enough color available, {} more\
                needed'.format(len(possible_types) - len(possible_colors)))
            print_color = False
        elif print_color:
            legend = ", ".join([possible_types[i] + " in " +
                                possible_colors[i] for i in
                                range(len(possible_types))])
        else:
            legend = ""
        print("Model description: " + legend)
        for _object in self.model:
            if print_color:
                _object.print(possible_colors[
                    possible_types.index(_object.type)])
            else:
                _object.print()
        if print_color:
            self.loss.print(possible_colors[
                possible_types.index(self.loss.type)])
        else:
            self.loss.print()

    def set_Lr(self, lr=0):
        for _object in self.model:
            if isinstance(_object, Linear):
                _object.set_Lr(lr)
