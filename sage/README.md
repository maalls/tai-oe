# Installation

dotnet

brew install --cask dotnet-sdk
echo 'export DOTNET_ROOT=/opt/homebrew/share/dotnet' >> ~/.zshrc
echo 'export PATH=$PATH:$DOTNET_ROOT:$DOTNET_ROOT/tools' >> ~/.zshrc
source ~/.zshrc
dotnet --info
