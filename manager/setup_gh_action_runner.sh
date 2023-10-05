# Sets up the manager-node as a github-action runner
# https://github.com/organizations/tess-atlas/settings/actions/runners/new


mkdir gh_actions_runner && cd gh_actions_runner
sudo yum install perl-Digest-SHA -y
sudo yum install libicu -y

curl -o actions-runner-linux-x64-2.309.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.309.0/actions-runner-linux-x64-2.309.0.tar.gz
echo "2974243bab2a282349ac833475d241d5273605d3628f0685bd07fb5530f9bb1a  actions-runner-linux-x64-2.309.0.tar.gz" | shasum -a 256 -c
echo "2974243bab2a282349ac833475d241d5273605d3628f0685bd07fb5530f9bb1a  actions-runner-linux-x64-2.309.0.tar.gz" | shasum -a 256 -c
tar xzf ./actions-runner-linux-x64-2.309.0.tar.gz
./config.sh --url https://github.com/tess-atlas --token ADXLBR5WWO4L5BXYQ54V6HTFDTMGS
