# Importing the libraries
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.optim as optim
import torch.utils.data
from sympy.codegen import Variable
from torch.autograd import Variable
from torch.nn import MSELoss

# Importing the dataset
movies = pd.read_csv('ml-1m\\movies.dat' , sep = '::' , engine = 'python' ,header = None , encoding="latin-1")
users = pd.read_csv('ml-1m\\users.dat' , sep = '::' , engine='python' , header = None , encoding="latin-1")
ratings = pd.read_csv('ml-1m\\ratings.dat' , sep = '::' , engine='python' , header = None , encoding="latin-1")

# Preparing the training set and the test set
training_set = pd.read_csv('ml-100k\\u1.base' , delimiter='\t')
training_set = np.array(training_set , dtype = 'int')
test_set = pd.read_csv('ml-100k\\u1.test' , delimiter='\t')
test_set = np.array(test_set , dtype = 'int')

# Getting the number of users and movies
nb_users = max (max(training_set[: ,0]) , max(test_set[: ,0]))
nb_movies = max (max(training_set[: ,1]) , max(test_set[: ,1]))

# Converting the data into an array with users in lines and movies in columns
def convert(data):
    new_data = []
    for id_user in range(1 , nb_users + 1):
        id_movie = data[:,1][data[:,0] == id_user]
        id_ratings = data[:, 2][data[:, 0] == id_user]
        ratings = np.zeros(nb_movies)
        ratings[id_movie - 1] = id_ratings
        new_data.append(ratings)
    return new_data
training_set = convert(training_set)
test_set = convert(test_set)

# Converting the data into torch tensors
training_set = torch.FloatTensor(training_set)
test_set = torch.FloatTensor(test_set)

# Converting the architecture of the neural network
class SAE(nn.Module):
    def __init__(self , ):
        super(SAE , self).__init__()
        self.fc1 = nn.Linear(nb_movies , 20)
        self.fc2 = nn.Linear(20 , 10)
        self.fc3 = nn.Linear(10, 20)
        self.fc4 = nn.Linear(20, nb_movies)
        self.activation = nn.Sigmoid()

    def forward(self, x):
        x  = self.activation(self.fc1(x))
        x = self.activation(self.fc2(x))
        x = self.activation(self.fc3(x))
        x = self.fc4(x)
        return x

sae = SAE()
criterion = nn.MSELoss()
optimizer = optim.RMSprop(sae.parameters() , lr = 0.01 , weight_decay = 0.5)

# Training the SAE
nb_epochs = 200
for epoch in range(1 , nb_epochs + 1):
    training_loss = 0
    s = 0.
    for id_user in range(nb_users):
        input =Variable(training_set[id_user]).unsqueeze(0)
        target = input.clone()
        if torch.sum(target.data > 0) > 0:
            output = sae(input)
            target.requires_grad = False
            output[target == 0] = 0
            loss = criterion(output , target)
            mean_corrector = nb_movies/float(torch.sum(target.data > 0) + 1e-10)
            loss.backward()
            training_loss += np.sqrt(loss.item()*mean_corrector)
            s += 1.
            optimizer.step()
    print('epoch ' + str(epoch) + ' loss ' + str(training_loss / s))

#  Testing the SAE
test_loss = 0
s = 0
for id_user in range(nb_users):
    input =Variable(training_set[id_user]).unsqueeze(0)
    target = Variable(test_set[id_user]).unsqueeze(0)
    if torch.sum(target.data > 0) > 0:
        output = sae(input)
        target.requires_grad = False
        output[target == 0] = 0
        loss = criterion(output , target)
        mean_corrector = nb_movies/float(torch.sum(target.data > 0) + 1e-10)
        test_loss += np.sqrt(loss.item()*mean_corrector)
        s += 1.
print('test loss ' + str(test_loss / s))