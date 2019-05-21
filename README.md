# pyper

Pipeline structure for concatenating functions with different parameters for analysis. Time and time again the same 
pipeline needs to be applied to similar datasets but with slightly different parameters. The main goal of this module is
 to be able to easily concatenate the desired functions into a pipeline and save the parameters used for each function.
 
## Usage
 
The Pipe class contains the different functions that are to be concatenated. When adding functions, it automatically 
converts them into AdaptedFunction class. Functions can be converted into AdaptedFunctions and parameters set or 
directly added to them. Another possibility is to add function to Pipe and later on set each of the parameters, as in 
the example below:
 
```
my_pipe = Pipe()
my_pipe + my_func_0
my_pipe + my_func_1
my_pipe.change_func_id('first_function', 'my_func_0')
my_pipe.change_func_id('second_function', 'my_func_1')
my_pipe.make_connection('first_function', 'second_function',provider_func_result=0, subscriber_func_parameter=1)
print(my_pipe)
```

In this example, a Pipeline is created and then two functions are added. The function identifier are renamed with 
the change_func_id method (new_name, old_name). Finally, the make_connection method is used to connect the first result
of the first function with the second parameter of the second function.

If you previously create the AdaptedFunction object, setting it's id and parameters, you can use the >> operator to add 
a new AdaptedFunction to the pipeline connecting the first result with the first parameter of the new function.

```
adapted_2 = AdaptedFunction(my_func_2, func_id='third_function')
adapted_2['b'] = 2
my_pipe >> adapted_2 

print(my_pipe)
```
