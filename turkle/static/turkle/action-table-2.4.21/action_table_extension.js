document.addEventListener('DOMContentLoaded', function() {
    const actionTableFilters = document.querySelector('action-table-filters');
    
    if (actionTableFilters) {
        actionTableFilters.addEventListener('action-table-filter', function(event) {
            const filterData = event.detail;
            const url = new URL(window.location);
            
            // Process each filter in the event detail
            Object.keys(filterData).forEach(filterKey => {
                const filterInfo = filterData[filterKey];
                
                // First, remove any existing parameters with this key
                url.searchParams.delete(filterKey);
                
                if (filterInfo && filterInfo.values && Array.isArray(filterInfo.values)) {
                    // Filter out empty/null values
                    const validValues = filterInfo.values.filter(value =>
                        value !== null && value !== undefined && value.toString().trim() !== ''
                    );
                    
                    // Add each valid value as a separate parameter
                    validValues.forEach(value => {
                        url.searchParams.append(filterKey, value);
                    });
                }
            });
            
            // Update the URL without reloading the page
            window.history.pushState({}, '', url.toString());
        });
    }

    const actionTable = document.querySelector('action-table');
        
        if (actionTable) {
          // Function to update URL parameters
          function updateURLParams() {
            const url = new URL(window.location);
            const sort = actionTable.getAttribute('sort');
            const direction = actionTable.getAttribute('direction');
            
            // Update or remove sort parameter
            if (sort) {
              url.searchParams.set('sort', sort);
            } else {
              url.searchParams.delete('sort');
            }
            
            // Update or remove direction parameter
            if (direction) {
              url.searchParams.set('direction', direction);
            } else {
              url.searchParams.delete('direction');
            }
            
            // Update browser history without reload
            window.history.pushState({}, '', url.toString());
          }
          
          // Create a MutationObserver to watch for attribute changes
          const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
              if (mutation.type === 'attributes' &&
                  (mutation.attributeName === 'sort' || mutation.attributeName === 'direction')) {
                updateURLParams();
              }
            });
          });
          
          // Start observing the action-table element for attribute changes
          observer.observe(actionTable, {
            attributes: true,
            attributeFilter: ['sort', 'direction']
          });
        }
});
