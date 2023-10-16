<a name="readme-top"></a>

<br />
<div align="center">
  <h1 align="center">Elastic Beanstalk Env Manager</h1>
  <h5 align="center">Script that simplifies managing environment variables for AWS Elastic Beanstalk apps</h5>
  <p align="center">
    <a href="https://github.com/benmotyka/elastic-beanstalk-env-manager/issues">Report Bug</a>
    ·
    <a href="https://github.com/benmotyka/elastic-beanstalk-env-manager/issues">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#usage">Usage</a></li>
      </ul>
    </li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>


## About The Project

Managing environment variables in AWS Elastic Beanstalk can be tiresome, especially when a project contains many of them. Whenever EB Environment is terminated, there is no way to simply persist or move them to another EB Environment. That's where this script comes in handy. It parses envs from a choosen file and injects them to the prepared one-liner. This way, envs for each EB Environment can be kept as a separate file, and all that is needed to do whenever they change is to run this script.

<br />

## Getting Started

### Prerequisites

- [AWS CLI (configured)](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

### Usage

1. Clone this repo and enter project
   ```sh
   git clone https://github.com/benmotyka/elastic-beanstalk-env-manager.git
   cd elastic-beanstalk-env-manager/
   ```
2. Create file containing envs (see .env.example):
   ```
    KEY1=value1
    KEY2=value2
   ```
3. Run script
   ```sh
   ./env-manager.sh <eb_environment_name> <relative_path_to_env_file>
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Ben Motyka - [LinkedIn](https://www.linkedin.com/in/ben-motyka-97a729240/) - benmotykax@gmail.com

Project Link: [https://github.com/benmotyka/elastic-beanstalk-env-manager](https://github.com/benmotyka/elastic-beanstalk-env-manager)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
