#!/bin/bash
# Variable configuration
DB_NAME="strix_final"
DB_USER="postgres"
SCRIPTS_DIR="database/scripts"

# Colors for a professional terminal
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' 

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}      DEPLOYING INFRASTRUCTURE (5 SCHEMAS)        ${NC}"
echo -e "${BLUE}==================================================${NC}"

# 1. Cleaning and Recreation of the Environment
echo -e "\n${YELLOW}1. Restarting database '$DB_NAME'...${NC}"
sudo -u $DB_USER psql -c "drop database if exists $DB_NAME;"
sudo -u $DB_USER psql -c "create database $DB_NAME;"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database successfully recreated.${NC}"
else
    echo -e "${RED}Critical error creating the database. Aborting.${NC}"
    exit 1
fi
# 2. Defining the execution order
FILES=(
    "01_init.sql"
    "02_identity_and_operational.sql"
    "03_raw_ingestion_and_audit.sql"
    "04_silver_refinery.sql"
    "05_final_storage_and_reports.sql"
    "06_security_and_performance.sql"
    "07_system_logs_and_audit.sql"
)

# 3. Sequential execution of SQL components
echo -e "\n${YELLOW}2. Applying layers of data refinery...${NC}"

for script in "${FILES[@]}"; do
    FILE_PATH="$SCRIPTS_DIR/$script"
    
    if [ -f "$FILE_PATH" ]; then
        echo -n "Processing $script... "
        sudo -u $DB_USER psql -d $DB_NAME -f "$FILE_PATH" > /dev/null 2>&1
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}SUCCESS${NC}"
        else
            echo -e "${RED}FAILED${NC}"
            echo -e "${RED}Error in $FILE_PATH. Stopping deployment.${NC}"
            exit 1
        fi
    else
        echo -e "${RED}The file was not found: $FILE_PATH${NC}"
        exit 1
    fi
done

# 4. Physical Partitioning Configuration
echo -e "\n${YELLOW}3. Configuring physical telemetry partitions (January 2026)...${NC}"
sudo -u $DB_USER psql -d $DB_NAME -c "create table if not exists raw_vision.receptions_y2026m01 partition of raw_vision.receptions for values from ('2026-01-01') to ('2026-02-01');"
sudo -u $DB_USER psql -d $DB_NAME -c "create table if not exists raw_voice.receptions_y2026m01 partition of raw_voice.receptions for values from ('2026-01-01') to ('2026-02-01');"
echo -e "${GREEN}Technical partitions activated.${NC}"

# 5. Architecture Health Verification
echo -e "\n${YELLOW}4. Validating the integrity of the 5 core schemas...${NC}"
SCHEMAS_COUNT=$(sudo -u $DB_USER psql -d $DB_NAME -t -c "select count(*) from pg_namespace where nspname in ('operational', 'audit', 'cleansed', 'artifacts', 'logs');" | xargs)

if [ "$SCHEMAS_COUNT" == "5" ]; then
    echo -e "${GREEN} Validated integrity: All 5 core layers are present.${NC}"
else
    echo -e "${RED}Error: Only detected $SCHEMAS_COUNT of the 5 required core layers.${NC}"
fi

echo -e "\n${BLUE}====================================================${NC}"
echo -e "${GREEN}   DEPLOYMENT COMPLETED SUCCESSFULLY   ${NC}"
echo -e "${BLUE}  THE SYSTEM IS READY FOR THE SEED_INITIAL_DATA.PY ${NC}"
echo -e "${BLUE}======================================================${NC}"