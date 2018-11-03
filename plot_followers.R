#!/usr/bin/env Rscript
require(ggplot2)
require(lubridate)

folder   <- '/var/www/html/followers/'

args     <- commandArgs(trailingOnly=TRUE)
username <- args[1]

readData <- function(path, colname){
  data <- read.csv(path, header=FALSE, sep=" ", col.names=c('date','time', colname))
  data <- within(data, {Date=as.POSIXct(paste(date, time))})
  data <- subset(data, select=c('Date', colname))
  return(data)
}

#read and format the data
followerData  <- readData(paste("./logs/", username ,"/followerNum.txt", sep=''), 'Followers')
followingData <- readData(paste("./logs/", username ,"/followingNum.txt", sep=''), 'Following')

created_time = format(max(followerData$Date))

# plot total followers over time
p1 <- ggplot(followerData, aes(x=Date, y=Followers)) + geom_line()
p1 <- p1 + geom_line(data=followingData, aes(x=Date, y=Following), color='gray')
p1 <- p1 + ggtitle(paste("Total Followers over Time\nCreated:", created_time))
filename = paste(folder,'all_time.png', sep='')
ggsave(filename, plot=p1)
#plot(p1)

# plot followers over last 30 days
cutoff = max(followerData$Date) - days(30)
p2 <- ggplot(followerData[followerData$Date >= cutoff,], aes(x=Date, y=Followers)) + geom_line()
#p2 <- p2 + geom_line(data=followingData[followingData$Date >= cutoff,], aes(x=Date, y=Following), color='gray')
p2 <- p2 + ggtitle(paste("Followers over the last 30 Days\nCreated:", created_time))
filename = paste(folder,'last_month.png', sep='')
ggsave(filename, plot=p2, width=7, height=3)
#plot(p2)

# plot following over last 30 days
p3 <- ggplot(followingData[followingData$Date >= cutoff,], aes(x=Date, y=Following)) + geom_line()
p3 <- p3 + ggtitle(paste("Number of Accounts followed over the last 30 Days\nCreated:", created_time))
filename = paste(folder,'last_month_following.png', sep='')
ggsave(filename, plot=p3, width=7, height=3)
#plot(p3)

xvals = as.numeric(readLines(paste(folder,'regression-days', sep='')))
#xvals = c(1,3)
for(x in xvals){
  interval = days(x)
  # plot a x day linear regression
  cutoff = max(followerData$Date) - interval
  current_data = followerData[followerData$Date > cutoff,]
  linear <- lm(Followers ~ Date, current_data)
  current_data$fit = fitted(linear)
  pred = data.frame(Date=seq(max(followerData$Date), max(followerData$Date) + interval, length = length(current_data$Date)))
  pred$Followers = predict(linear, newdata = pred)

  p2 <- ggplot()
  p2 <- p2 + geom_point(aes(x=Date, y=Followers), current_data)
  p2 <- p2 + geom_line(aes(x=Date, y=fit), current_data)
  p2 <- p2 + geom_line(aes(x=Date, y=Followers), pred, linetype="dashed")
  p2 <- p2 + ggtitle(paste(x,'day prediction using linear regression over the last',x,'days\nCreated:', created_time))
  filename = paste(folder,x,'-day-regression.png', sep='')
  ggsave(filename, plot=p2)

  # plot the last x day linear regression and compare it to current data
  midpoint = max(followerData$Date) - interval
  cutoff = midpoint - interval
  old_data = followerData[followerData$Date >= cutoff & followerData$Date <= midpoint,]
  new_data = followerData[followerData$Date >= midpoint,]
  linear <- lm(Followers ~ Date, old_data)
  old_data$fit = fitted(linear)
  new_data$fit = predict(linear, newdata = new_data)

  p3 <- ggplot()
  p3 <- p3 + geom_point(aes(x=Date, y=Followers), new_data, col="dark gray")
  p3 <- p3 + geom_point(aes(x=Date, y=Followers), old_data)
  p3 <- p3 + geom_line(aes(x=Date, y=fit), old_data)
  p3 <- p3 + geom_line(aes(x=Date, y=fit), new_data, linetype="dashed")
  p3 <- p3 + ggtitle(paste('Last',x,'day prediction compared to the data of the last',x,'days\nCreated:', created_time))
  filename = paste(folder,x,'-day-regression-prev.png', sep='')
  ggsave(filename, plot=p3)
}

# Avarage Growth
movingAverage<-function(data, time){
  data$avg <- NA
  for(i in c(1:length(data$avg))){
    cd <- data$Date[i]
    cf <- data$Followers[i]
    p <- subset(data, Date<cd-time)
    last_row <- length(p$Date)
    pd <- p$Date[last_row]
    pf <- p$Followers[last_row]
    
    if(last_row>0){
      data$avg[i] <- ((cf-pf)/((cd-pd)/ddays(1)))
    }
  }
  return(data)
}

p <- ggplot()
p <- p + geom_line(aes(x=Date, y=avg, color='1 Day'), subset(movingAverage(followerData, days(1)),!is.na(avg)))
p <- p + geom_line(aes(x=Date, y=avg, color='5 Days'), subset(movingAverage(followerData, days(5)),!is.na(avg)))
#p <- p + geom_line(aes(x=Date, y=avg, color='10 Days'), subset(movingAverage(followerData, days(10)),!is.na(avg)))
#p <- p + geom_point(aes(x=Date, y=avg, color='1 Hour'), subset(movingAverage(followerData, hours(1)),!is.na(avg)))
p <- p + ggtitle(paste('Moving Avarages in Growth over different Timeframes\nCreated:', created_time))
p <- p + labs(y ='Followers/Day', color = "Avarages")
filename = paste(folder,'growth.png', sep='')
ggsave(filename, plot=p)