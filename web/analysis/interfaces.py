from abc import ABC, abstractmethod

class ReportGeneratorInterface(ABC):
    @abstractmethod
    def generate(self, data: dict, input_path: str = None) -> str:
        """
        Generates a readable report based on the provided data.
        
        Args:
            data (dict): A dictionary containing analysis results.
            input_path (str, optional): Path to the original input file.
            
        Returns:
            str: The generated report content.
        """
        pass
