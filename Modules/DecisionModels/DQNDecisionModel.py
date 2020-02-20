import numpy as np
import random

from collections import deque

import torch
from torch import nn
from torch.autograd import Variable

from Modules.DecisionModels.BaseDecisionModel import BaseDecisionModel


class DQNModel(BaseDecisionModel):
    """
        Q-table module - using the DQN algorithm to return an action.
        """
    def __init__(self,
                 number_of_features,
                 number_of_actions,
                 gamma=0.9,
                 batch_size=16,
                 memory_size=10000):
        """
        Initializing the DQN module
        :param number_of_features: number of features.
        :param number_of_actions: number of actions
        :param gamma: discount factor
        :param batch_size: the batch size for training the network.
        :param memory_size: the memory size (where all the feedback and actions are stored)
        """
        BaseDecisionModel.__init__(self)

        self.dqn = DQN(number_of_features, number_of_actions)

        # The optimizer.
        self.optimizer = torch.optim.Adam(self.dqn.parameters, lr=1e-3)

        # The depth of the experience_replay.
        self.memory_size = memory_size

        # The memory where all the experience is stored (and used to train the network).
        self.replay_memory = ReplayMemory(memory_size)

        # The number of possible actions.
        self.number_of_actions = number_of_actions

        # The batch size for the training
        self.batch_size = batch_size

        # The discount factor.
        self.gamma = gamma

    def update_model(self, previous_state, previous_action, reward, state, _, done):
        """
        Updating the experience_replay memory and training the network.
        :param state: current state
        :param reward: current reward
        :param previous_state: previous state
        :param previous_action: previous action
        :param done: done status
        """

        if done:
            reward = -200

        # Updating experience_replay.
        self.replay_memory.push(previous_state, previous_action, reward, state, done)

        # Training if we have enough examples.
        if len(self.replay_memory) > self.batch_size:
            self.train()

    def train(self):
        """
        Training the neural network with the sample.
        """

        # Sampling from the experience replay.
        state, action, reward, new_state, done = self.replay_memory.sample(self.batch_size)

        # Computing q values.
        q_values = reward + (1-done) * self.gamma * self.dqn.get_values(new_state)

        # Computing the approximation of the target from the sample.
        predicted_q_values = self.dqn.predict_q_values(state, action)

        # Backward pass.
        self.optimizer.zero_grad()

        # Defining the loss - MSE(approximation, target).
        loss = self.dqn.compute_loss(predicted_q_values, q_values)
        loss.backward()
        self.optimizer.step()

    def get_action(self, state):
        """
        Get the action according to the DQN algorithm.
        :param state: the relevant state.
        :return: the action according to the DQN algorithm.
        """
        return self.dqn.get_action_with_max_value(state)

    def get_random_action(self):
        """
        Get a random action.
        :return: a random action
        """

        return random.randint(0, self.number_of_actions - 1)


class DQN(object):

    def __init__(self, number_of_features, number_of_actions):
        # The neural network module.
        self.neural_network = nn.Module()

        # Initializing the neural network module.
        self.neural_network.__init__()

        # The neural networks layers and activation function.
        self.neural_network.f1 = nn.Linear(number_of_features, 40)
        self.neural_network.f2 = nn.Linear(40, 100)
        self.neural_network.f3 = nn.Linear(100, number_of_actions)
        self.neural_network.relu = nn.ReLU()

        # The metric used to optimize.
        self.neural_network.mse = nn.MSELoss()

    def forward(self, state):
        """
        Forward pass of the neural network.
        :param state: the state
        :return: the estimate of Q for the state.
        """
        out = self.neural_network.f1(state)
        out = self.neural_network.relu(out)
        out = self.neural_network.f2(out)
        out = self.neural_network.relu(out)
        out = self.neural_network.f3(out)

        return out

    def get_values(self, state):

        return np.max(self.forward(Variable(torch.from_numpy(state).float())).data.numpy())

    def predict_q_values(self, state, action):

        s = torch.from_numpy(state).float()
        a = torch.from_numpy(action)

        return self.forward(Variable(s)).gather(1, Variable(a.unsqueeze(1)))

    def get_action_with_max_value(self, state):

        np.argmax(self.forward(torch.from_numpy(state).float()).data.numpy())

    @property
    def parameters(self):
        return self.neural_network.parameters()

    def compute_loss(self, approximation, target):
        return self.neural_network.mse(approximation, target)


class ReplayMemory(object):

    def __init__(self, memory_size):
        self.memory_size = memory_size
        self.memory = list()
        self.position = 0

    def push(self, previous_state, previous_action, reward, state, done):
        """Saves a transition."""
        if len(self.memory) < self.memory_size:
            self.memory.append(None)

        self.memory[self.position] = (previous_state, previous_action, reward, state, done)
        self.position = (self.position + 1) % self.memory_size

    def sample(self, batch_size):

        random_sample = np.stack(random.sample(self.memory, batch_size)).T

        state = np.stack(random_sample[0])
        action = random_sample[1].astype(int)
        reward = random_sample[2].astype(int)
        new_state = np.stack(random_sample[3])
        done = random_sample[4]

        return state, action, reward, new_state, done

    def __len__(self):
        return len(self.memory)