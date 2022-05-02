# Sol Binder

A tool for working with solidity contracts

## Installation
Install sol-binder
```
pip install sol-binder
```

## CLI Quickstart
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

### 4. Reading from the contract
Reading is done with the call subcommand
The result is printed to STDOUT
```
sol-binder call 'nft.sol' getOwner
```
Function arguments are given as additional cli arguments
```
sol-binder call 'nft.sol' getOwnerOf 12
```
Each call argument given on the command-line is treated as JSON formatted data. Meaning specifying "12" on the command line will result as the integer 12, but specifying '"12"' (or \"12\", depending on your shell) will be the string "12". The same applies to lists and other JSON data types: specifying "[1,2,3]" means transferring a list of integers as one of the arguments to the call.
```
sol-binder call 'nft.sol' markVoted "[1,2,3,4]"
```

### 5. Writing to contracts
Use the transact subcommand
```
sol-binder transact "erc-20.sol" mint 10000000000
```

## Python Module Quickstart
Using the sol_binder python module programatically you can do everything you can with the CLI, and more.

### 1. Creating a project
When using sol-binder programatically you can instantiate the ProjectConfig yourself as opposed to having built-in sol-binder functions build it from the `solbinder.yaml` file.
If you wish to save it to a file its up to you.

For example - here is a default config
```
from sol_binder.project.config import ProjectConfig
project_config = ProjectConfig()
```

If you still want to use the `solbinder.yaml` file, that's fine, use the ProjectConfig.load() function:
```
from sol_binder.project.config import ProjectConfig
project_config = ProjectConfig.load()
```

### 2. Deploying contracts
In order to deploy contracts you must either configure a deployment plan in the `project_config` you've instantiated or make sure there are contract files in the directory specified in `project_config.contract_dir`

####  Creating your own deployment in-memory
The structure of the deployments dict is the same as specified for the `solbinder.yaml` file's `deployments:` configuration value
```
from sol_binder.project.config import ProjectConfig
project_config = ProjectConfig(
  deployments = {"nft.sol": []}  
)
```

#### Deploying contracts
```
from sol_binder.commands.deploy import deploy_contract

deploy_contract("nft.sol", deploying_account, private_key, solc_version, project_config)
```