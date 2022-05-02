# Sol Binder

A tool for working with solidity contracts

## Quickstart
### 0. Create a blank project
Install sol-binder
```
pip install sol-binder
```
### 1. Create a blank project
Choose a directory to contain your project and run the command
```
sol-binder init
```
This creates a default project configuration file called `solbinder.yaml`.

Sol-Binder locates the project root folder based on the location of the `solbinder.yaml`, similar to how git locates the repo root,
so you can run `sol-binder` from any subdirectory of the project. 

### 2. Make sure to configure your target blockchain network
Edit the `solbinder.yaml` file and make sure the `networks:` section points to the correct block-chains

By default there is only one network called `dev` and that network points to a local running block-chain on `localhost:8545` with the network id of `1337`

Default `networks:` section:
```
networks:
  dev:
    host: localhost
    network_id: 1337
    port: 8545
```


### 3. Add contracts
Place your solidity contracts in the `contracts` folder created by the init command

By default, sol-binder will autodetect contracts based on the ".sol" files located in the `contracts` folder and you can immediately deploy them to the `dev` network

For example if you have `contracts/mycontract.sol` you can do:
```
sol-binder deploy mycontract.sol
```

You can also deploy all contracts at once by running
```
sol-binder deploy
```

To deploy a contract multiple times or to specify constructor arguments, specify them in the `deployments:` section of `solbinder.yaml`.

There are two possible ways to list a contract deployment

#### 1. Single contract deployment with or without constructor arguments
```
deployments:
  "erc-721.sol": []
  "erc-20.sol" ["My coin", "$MYX", 10000000000000]
```

In this way, contracts are referred by their filename:
```
sol-binder deploy erc-721.sol
sol-binder deploy erc-20.sol
```


#### 2. Multiple deployments of the same contract. Each deployment must have a unique name
```
deployments:
    "erc-20.sol":  # Deploy the same contract multiple times with different args
        "coin1": ["My coin 1", "$MnX", 10000000000000]
        "coin2": ["My coin 2", "$MzX", 2000000]
```

