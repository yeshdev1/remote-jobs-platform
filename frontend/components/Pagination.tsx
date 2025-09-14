interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export default function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5; // Show at most 5 page numbers
    
    if (totalPages <= maxPagesToShow) {
      // If we have 5 or fewer pages, show all of them
      for (let i = 0; i < totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always include first page
      pages.push(0);
      
      // Calculate start and end of page range
      let startPage = Math.max(1, currentPage - 1);
      let endPage = Math.min(totalPages - 2, currentPage + 1);
      
      // Adjust if we're near the beginning
      if (currentPage < 2) {
        endPage = 3;
      }
      
      // Adjust if we're near the end
      if (currentPage > totalPages - 3) {
        startPage = totalPages - 4;
      }
      
      // Add ellipsis after first page if needed
      if (startPage > 1) {
        pages.push(-1); // -1 represents ellipsis
      }
      
      // Add middle pages
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      
      // Add ellipsis before last page if needed
      if (endPage < totalPages - 2) {
        pages.push(-2); // -2 represents ellipsis
      }
      
      // Always include last page
      pages.push(totalPages - 1);
    }
    
    return pages;
  };

  return (
    <nav className="flex items-center justify-center mt-8 mb-4">
      <ul className="flex space-x-2">
        {/* Previous page button */}
        <li>
          <button
            onClick={() => currentPage > 0 && onPageChange(currentPage - 1)}
            disabled={currentPage === 0}
            className={`px-3 py-1 rounded-md ${
              currentPage === 0
                ? 'bg-gray-700/50 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600/30 text-blue-300 border border-blue-500/30 hover:bg-blue-600/50'
            }`}
            aria-label="Previous page"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        </li>
        
        {/* Page numbers */}
        {getPageNumbers().map((pageNumber, index) => (
          <li key={index}>
            {pageNumber < 0 ? (
              // Ellipsis
              <span className="px-3 py-1 text-gray-400">...</span>
            ) : (
              // Page number
              <button
                onClick={() => onPageChange(pageNumber)}
                className={`px-3 py-1 rounded-md ${
                  currentPage === pageNumber
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                    : 'bg-white/10 backdrop-blur-sm text-gray-200 hover:bg-white/20'
                }`}
                aria-label={`Page ${pageNumber + 1}`}
                aria-current={currentPage === pageNumber ? 'page' : undefined}
              >
                {pageNumber + 1}
              </button>
            )}
          </li>
        ))}
        
        {/* Next page button */}
        <li>
          <button
            onClick={() => currentPage < totalPages - 1 && onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages - 1}
            className={`px-3 py-1 rounded-md ${
              currentPage >= totalPages - 1
                ? 'bg-gray-700/50 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600/30 text-blue-300 border border-blue-500/30 hover:bg-blue-600/50'
            }`}
            aria-label="Next page"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          </button>
        </li>
      </ul>
    </nav>
  );
}
