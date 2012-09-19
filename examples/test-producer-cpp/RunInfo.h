// ****************************************************************************
//
/// @filename: RunInfo.h
///
///  @author: D. Reitz
///
///  @date: 19-Sept-2012
///
///  @summary: Class for run information
/// 
// *****************************************************************************

#include <string>

namespace Adara
{
namespace Utils
{

class RunInfo
{
protected:
   std::string m_ipts;
   std::string m_instrument;
   unsigned long m_runNumber;
   std::string m_datafile;

public:

   
   RunInfo( const std::string& ipts, const std::string& instrument,
            unsigned long runNumber, const std::string& datafile="optional")
   : m_ipts(ipts), m_instrument(instrument), m_runNumber(runNumber), m_datafile(datafile) {}

   /// @brief returns data dictionary string for passing
   /// 
   /// Example {"ipts": "IPTS-5678", "instrument": "HYSA", "data_file": "the-file-name", "run_number": 9999}
   std::string getDict() const
   {
      std::ostringstream oss;
      oss << "{\"ipts\": \"" <<  m_ipts << "\", \"instrument\": \""<< m_instrument <<"\", \"data_file\": \"" <<
                       m_datafile<< "\", \"run_number\": " <<m_runNumber<<"}";
      return oss.str();
   }

};


}
}

