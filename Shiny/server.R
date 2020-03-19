function(input, output) {
  
  dados <- read.csv2("dados.csv")
    output$distPlot <- renderPlot({
        # generate bins based on input$bins from ui.R
        x    <- dados[, input$teste]
        bins <- seq(min(x), max(x), length.out = input$bins + 1)

        # draw the histogram with the specified number of bins
        hist(x, breaks = bins, col = 'darkgray', border = 'white')
    })
    
    output$media <- renderText(mean(dados$Casos))
    output$teste <- renderText(input$teste)
}
