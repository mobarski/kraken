# Kraken

Kraken is a Contextual Bandits engine designed for:

- Simplicity: Easy to use and understand.
- Ease of deployment: Quickly deployable on various platforms with minimal configuration.
- Ease of scaling: Designed to be AWS lambda friendly, making it scalable and efficient.

Features include multiple experiments (also known as rooms) and segmentation for more granular control and analysis.



## Installation

**NOTE**: This is experimental software. The design, functionality, and interface can change without any notice.

To install Kraken, you can use the pip command as follows:

```
TODO: pip install git+https://github.com/mobarski/kraken.git
```



## Glossary



**arm** - An option or variant in a multi-armed bandit experiment. Each arm represents a different version of a product,  feature, or strategy.

**room** - A term used to denote a unique experiment or test scenario within the Kraken system. Each room can contain multiple arms.

**pool** - A set of arms available in a specific room. It represents the different variations of an experiment that are  currently active.

**view** - The action of a user seeing or being presented with a variant (arm). This is tracked to understand the  exposure of each arm in the experiment.

**click** - The action of a user interacting with or choosing a variant (arm). This is an indication of preference and is  used to adjust the probability distribution of the arms.

**context** - The information about the current situation of a user. This can include user attributes, time of day, location, and more. The context is used to personalize the experience for each user.

**segment** - A subset of the context that is defined by a specific set of characteristics. Each segment has separate tracking of statistics (clicks/views) allowing for more targeted analysis and personalization.



## Diagrams



### Calculate CTR

```mermaid
sequenceDiagram

loop arm_ids
core ->> db : GET views:@arm
core ->> db : GET clicks:@arm
core ->> db : SET ctr:@arm

loop ctx_items
core ->> db : GET views-ctx:@arm:@ctx
core ->> db : GET clicks-ctx:@arm:@ctx
core ->> db : SET ctr-ctx:@arm:@ctx
end

end



```



### Calculate UCB1

```mermaid
sequenceDiagram

core ->> db : GET views-agg

loop arm_ids
core ->> db : GET views:@arm
core ->> db : GET clicks:@arm
core ->> db : SET ucb1:@arm

loop ctx_items
core ->> db : GET views-ctx:@arm:@ctx
core ->> db : GET clicks-ctx:@arm:@ctx
core ->> db : SET ucb1-ctx:@arm:@ctx
end

end
```

### Calculate BUCB (Bayesian UCB)



## References
