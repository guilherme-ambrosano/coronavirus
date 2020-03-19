library(shiny)

fluidPage(

    # Application title
    titlePanel("Casos de coronavirus no Brasil"),

    # Sidebar with a slider input for number of bins 
    sidebarLayout(
        sidebarPanel(
            sliderInput("bins", "Number of bins:", min = 1, max = 50, value = 30),
            selectInput("teste", "escolhe ae", c("Casos", "Dia", "Mes"))
        ),

        # Show a plot of the generated distribution
        mainPanel(
           plotOutput("distPlot"),
           textOutput("media"),
           textOutput("teste")
        )
    )
)

