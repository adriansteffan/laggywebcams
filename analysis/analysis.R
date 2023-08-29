library(tidyverse)

PREPROCESSING_PATH <- file.path("..", "preprocessing")
DATA_DIR <- file.path(PREPROCESSING_PATH, "output")

webgazer <- read.csv(file.path(DATA_DIR, 'webgazer_data.csv'))
webgazer_resampled <- read.csv(file.path(DATA_DIR, 'webgazer_RESAMPLED_data.csv'))
webgazer_norec <- read.csv(file.path(DATA_DIR, 'webgazer_norec_data.csv'))
webgazer_norec_resampled <- read.csv(file.path(DATA_DIR, 'webgazer_norec_RESAMPLED_data.csv'))

exctract_lookingscore_per_timepoint = function(resampled_data){
  return(resampled_data %>%
           group_by(t) %>% 
           summarize(lookingscore = sum(grepl("target", hit, fixed = TRUE), na.rm = TRUE) / sum(grepl("target", hit, fixed = TRUE) | grepl( "distractor", hit, fixed = TRUE)))
  )
}

## assumes aoi comparison or everything, side comparison ommited
webgazer_resampled <- webgazer_resampled %>% mutate(hit=aoi_hit)
webgazer_norec_resampled <- webgazer_norec_resampled %>% mutate(hit=aoi_hit)

webgazer_ls_over_time <- exctract_lookingscore_per_timepoint(webgazer_resampled) %>% mutate(tracker='webgazer')
webgazer_norec_ls_over_time <- exctract_lookingscore_per_timepoint(webgazer_norec_resampled) %>% mutate(tracker='webgazer_norec')

ls_over_time <- do.call("rbind", list(
  webgazer_ls_over_time,
  webgazer_norec_ls_over_time
)) %>% spread(key = tracker, value = lookingscore)


plot(ls_over_time$t, ls_over_time$webgazer, type = "l", col="red", xlab="Time since Stimulus Video Start (ms)", ylab="Sample's Mean Looking Score", ylim = c(0.0, 1.0))
lines(ls_over_time$t, ls_over_time$webgazer_norec,col="green")
abline(v=26000, col="blue")
abline(v=30000, col="blue")
abline(h=0.5, col="blue")
legend(2000, 0.9, legend=c("WebGazer no recording", "WebGazer"),
       col=c("green", "red"), lty=1:1, cex=0.8)

## TODO: Do more precise analyses once the pilot data is here