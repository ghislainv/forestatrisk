import deforestprob as dfp

# List of countries to process
countries = ["Senegal", "Gambia", "Guinea-Bissau", "Guinea", "Sierra-Leone",
             "Liberia", "Côte D'Ivoire", "Ghana",
             "Togo", "Benin", "Nigeria", "Cameroon",
             "Central African Republic",
             "Equatorial Guinea", "Gabon", "Uganda", "Kenya",
             "Tanzania", "Rwanda", "Burundi", "Madagascar",
             "Mozambique"]

# Country data
proj_africa = "EPSG:3395"
dfp.data.country(iso3="SLE", proj=proj_africa)

# End
