INCS += `activemqcpp-config --includes`
LIBS += `activemqcpp-config --libs`
SOURCES := $(shell ls *.cpp)

OBJS = $(SOURCES:.cpp=.o)

all: clean $(OBJS)
	g++ -g $(OBJS) $(LIBS) -o test-producer


%.o : %.cpp
	g++ -g -c $(CFLAGS) $(CPPFLAGS) ${INCS} $< -o $@

clean:
	rm -f $(OBJS) test-producer
	
