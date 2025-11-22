#!/bin/bash
# 残りのOptional Chainingを修正

FILE="map_complete_integrated_fixed.html"

# Line 2349: c?.center
sed -i "2349s/c?\\.center/(c \&\& c.center)/g" "$FILE"

# Line 2401: currentCity?.flow?.nearby_regions
sed -i "2401s/currentCity?\\.flow?\\.nearby_regions/(currentCity \&\& currentCity.flow \&\& currentCity.flow.nearby_regions)/g" "$FILE"

# Line 2479: k.labels?.[i]
sed -i "2479s/k\\.labels?\\.\\\[i\\\]/(k.labels \&\& k.labels[i])/g" "$FILE"

# Line 2843-2847: qs()?.selectedOptions (5箇所)
sed -i "2843s/qs('#difficultyFilter')?\\.selectedOptions/(qs('#difficultyFilter') \&\& qs('#difficultyFilter').selectedOptions)/g" "$FILE"
sed -i "2844s/qs('#ageGroupFilter')?\\.selectedOptions/(qs('#ageGroupFilter') \&\& qs('#ageGroupFilter').selectedOptions)/g" "$FILE"
sed -i "2845s/qs('#genderFilter')?\\.selectedOptions/(qs('#genderFilter') \&\& qs('#genderFilter').selectedOptions)/g" "$FILE"
sed -i "2846s/qs('#qualificationFilter')?\\.selectedOptions/(qs('#qualificationFilter') \&\& qs('#qualificationFilter').selectedOptions)/g" "$FILE"
sed -i "2847s/qs('#residenceFilter')?\\.selectedOptions/(qs('#residenceFilter') \&\& qs('#residenceFilter').selectedOptions)/g" "$FILE"

# Line 2989-3013: options?.property (8箇所)
sed -i "2989s/options?\\.limit/(options \&\& options.limit)/g" "$FILE"
sed -i "2991s/options?\\.exclude/(options \&\& options.exclude)/g" "$FILE"
sed -i "2992s/options?\\.keys/(options \&\& options.keys)/g" "$FILE"
sed -i "2992s/options?\\.maxColumns/(options \&\& options.maxColumns)/g" "$FILE"
sed -i "3010s/options?\\.rowLabel/(options \&\& options.rowLabel)/g" "$FILE"
sed -i "3011s/options?\\.columnLabel/(options \&\& options.columnLabel)/g" "$FILE"
sed -i "3012s/options?\\.chartId/(options \&\& options.chartId)/g" "$FILE"
sed -i "3013s/options?\\.chartTitle/(options \&\& options.chartTitle)/g" "$FILE"

# Line 4086: (c.overview && c.overview.kpis)?.find
sed -i "4086s/(c\\.overview && c\\.overview\\.kpis)?\\.find/((c.overview \&\& c.overview.kpis) \&\& (c.overview.kpis).find)/g" "$FILE"

# Line 4191: regionOptions?.prefectures?.length
sed -i "4191s/regionOptions?\\.prefectures?\\.length/(regionOptions \&\& regionOptions.prefectures \&\& regionOptions.prefectures.length)/g" "$FILE"

echo "All remaining optional chaining fixed"
