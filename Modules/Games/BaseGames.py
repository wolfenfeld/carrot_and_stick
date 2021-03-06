from Modules.DecisionModels.BaseDecisionModel import Transition


class BaseGame(object):
    """
    Game - The object that defines the game.
    """
    def __init__(self, agent, world, episodes):
        """
        Initialization of the Game object
        :param agent: the agents that play the game
        :param world: the world where the game is played
        :param episodes: the number of episodes that will be played in the game.
        """
        self.agent = agent
        self.world = world
        self.episodes = episodes

        # The best total reward over all the episodes.
        self.best_total_reward = 0

    def run(self):
        """
        run function - Running a game
        """
        # The total rewards of each episode.
        rewards = dict()

        for episode in range(1, self.episodes + 1):

            # The total reward for the current episode.
            total_reward = 0

            # The initial state
            state = self.world.reset()

            while True:
                # if episode > self.episodes - 300:
                # self.world.render()

                # Sampling the action from the agent.
                action = self.agent.get_action(state)

                # Interacting with the world and acquiring the feedback:
                # the new state, the reward and the done indicator.
                next_state, reward, done = self.world.interact_with_world(action)

                transition = Transition(state=state, action=action, reward=reward, next_state=next_state, done=done)
                # Updating the total reward.
                total_reward += reward

                self.agent.number_of_episodes_played += 1
                # Updating the agent
                self.agent.reinforce(transition)

                state = next_state

                # If the episode is done.
                if done:

                    # Updating the reward dictionary.
                    rewards[episode] = total_reward

                    # Keeping best reward.
                    self.best_total_reward = max(total_reward, self.best_total_reward)

                    print('Episode {0} is done.'.format(episode))
                    print('Total Reward : {0}, Best reward : {1}'.format(total_reward, self.best_total_reward))

                    break

        print('Rewards History for {0}'.format(self.world.env_name))
        print(rewards.values())
        score_interval = 50
        print('Average reward of last {0} runs'.format(score_interval))
        print(sum(list(rewards.values())[-score_interval:]) / len(list(rewards.values())[-score_interval:]))

        return rewards

    @property
    def agent_model(self):
        return self.agent.decision_model
