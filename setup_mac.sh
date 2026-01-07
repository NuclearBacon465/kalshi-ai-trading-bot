#!/bin/bash
# 🚀 Kalshi AI Trading Bot - Mac Installation Script
# This script sets up everything you need to run the bot on your Mac

set -e  # Exit on error

echo "================================================================="
echo "🚀 Kalshi AI Trading Bot - Mac Installation"
echo "================================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check Python version
echo -e "${BLUE}[1/10] Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    echo "Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
    echo -e "${RED}❌ Python 3.11+ required, you have $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION installed${NC}"
echo ""

# Step 2: Check for required tools
echo -e "${BLUE}[2/10] Checking required tools...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed${NC}"
    echo "Please install Git from https://git-scm.com/downloads"
    exit 1
fi
echo -e "${GREEN}✅ Git installed${NC}"
echo ""

# Step 3: Create virtual environment if it doesn't exist
echo -e "${BLUE}[3/10] Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi
echo ""

# Step 4: Activate virtual environment
echo -e "${BLUE}[4/10] Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Step 5: Upgrade pip
echo -e "${BLUE}[5/10] Upgrading pip...${NC}"
pip install --upgrade pip &> /dev/null
echo -e "${GREEN}✅ Pip upgraded${NC}"
echo ""

# Step 6: Install dependencies
echo -e "${BLUE}[6/10] Installing dependencies (this may take a few minutes)...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  No requirements.txt found, installing core dependencies...${NC}"
    pip install aiohttp aiosqlite cryptography pydantic httpx openai numpy structlog json-repair
    echo -e "${GREEN}✅ Core dependencies installed${NC}"
fi
echo ""

# Step 7: Setup API keys
echo -e "${BLUE}[7/10] Setting up API keys...${NC}"
echo ""
echo -e "${YELLOW}You need TWO API keys:${NC}"
echo "  1. Kalshi API Key & Private Key"
echo "  2. xAI API Key (for Grok)"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    touch .env
fi

# Check if keys are already configured
if grep -q "KALSHI_API_KEY=" .env && grep -q "XAI_API_KEY=" .env; then
    echo -e "${GREEN}✅ API keys already configured in .env${NC}"
    echo ""
    read -p "Do you want to reconfigure them? (y/N): " reconfigure
    if [[ ! $reconfigure =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Skipping API key configuration${NC}"
    else
        # Reconfigure
        echo ""
        read -p "Enter your Kalshi API Key: " kalshi_key
        sed -i '' '/KALSHI_API_KEY=/d' .env 2>/dev/null || sed -i '/KALSHI_API_KEY=/d' .env
        echo "KALSHI_API_KEY=$kalshi_key" >> .env

        read -p "Enter your xAI API Key: " xai_key
        sed -i '' '/XAI_API_KEY=/d' .env 2>/dev/null || sed -i '/XAI_API_KEY=/d' .env
        echo "XAI_API_KEY=$xai_key" >> .env

        echo -e "${GREEN}✅ API keys updated${NC}"
    fi
else
    echo ""
    read -p "Enter your Kalshi API Key: " kalshi_key
    echo "KALSHI_API_KEY=$kalshi_key" >> .env

    read -p "Enter your xAI API Key: " xai_key
    echo "XAI_API_KEY=$xai_key" >> .env

    echo -e "${GREEN}✅ API keys saved to .env${NC}"
fi
echo ""

# Step 8: Setup Kalshi private key
echo -e "${BLUE}[8/10] Setting up Kalshi private key...${NC}"
if [ -f "kalshi_private_key" ]; then
    echo -e "${GREEN}✅ kalshi_private_key file exists${NC}"

    # Check permissions
    PERMS=$(stat -f "%OLp" kalshi_private_key 2>/dev/null || stat -c "%a" kalshi_private_key)
    if [ "$PERMS" != "600" ]; then
        echo -e "${YELLOW}⚠️  Fixing file permissions...${NC}"
        chmod 600 kalshi_private_key
        echo -e "${GREEN}✅ Permissions set to 600 (secure)${NC}"
    else
        echo -e "${GREEN}✅ Permissions already secure (600)${NC}"
    fi
else
    echo -e "${RED}❌ kalshi_private_key file not found${NC}"
    echo ""
    echo "You need to create this file with your Kalshi private key:"
    echo "  1. Go to https://kalshi.com/account/api"
    echo "  2. Generate or download your private key"
    echo "  3. Save it as 'kalshi_private_key' in this directory"
    echo "  4. Run this script again"
    echo ""
    exit 1
fi
echo ""

# Step 9: Create logs directory
echo -e "${BLUE}[9/10] Setting up directories...${NC}"
mkdir -p logs
echo -e "${GREEN}✅ Logs directory created${NC}"
echo ""

# Step 10: Run verification tests
echo -e "${BLUE}[10/10] Running verification tests...${NC}"
echo -e "${YELLOW}This will test your API keys and setup...${NC}"
echo ""

if [ -f "test_your_actual_setup.py" ]; then
    python3 test_your_actual_setup.py
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ Verification tests passed!${NC}"
    else
        echo ""
        echo -e "${RED}❌ Verification tests failed${NC}"
        echo -e "${YELLOW}Please check your API keys and try again${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  test_your_actual_setup.py not found, skipping verification${NC}"
fi

echo ""
echo "================================================================="
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "================================================================="
echo ""
echo "Next steps:"
echo ""
echo -e "${BLUE}1. View your current balance:${NC}"
echo "   python3 monitor_trades.py --check-balance"
echo ""
echo -e "${BLUE}2. Test the bot (paper trading):${NC}"
echo "   python3 beast_mode_bot.py"
echo ""
echo -e "${BLUE}3. Launch the dashboard:${NC}"
echo "   python3 beast_mode_bot.py --dashboard"
echo ""
echo -e "${BLUE}4. Start live trading (REAL MONEY):${NC}"
echo "   python3 beast_mode_bot.py --live"
echo ""
echo -e "${BLUE}5. Monitor trades in real-time:${NC}"
echo "   python3 monitor_trades.py --watch"
echo ""
echo -e "${YELLOW}⚠️  WARNING: --live mode uses REAL MONEY!${NC}"
echo "   Test in paper mode first!"
echo ""
echo "================================================================="
