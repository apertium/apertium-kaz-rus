/*
 * A C++ I/O streams interface to the zlib gz* functions
 *
 * by Ludwig Schwardt <schwardt@sun.ac.za>
 * original version by Kevin Ruland <kevin@rodin.wustl.edu>
 *
 * This version isn't exactly like original, thus its incorporate new methods (like seekg)
 */

#ifndef ZFSTREAM_H
#define ZFSTREAM_H

#include <istream>
#include <ostream>
#include <zlib.h>

using namespace std;

class gzfilebuf : public std::streambuf
{
	public:
		// Constructor and destructor
		gzfilebuf();
		virtual ~gzfilebuf();
		
		// Methods and functions
		int setcompression(int comp_level, int comp_strategy = Z_DEFAULT_STRATEGY);
		bool is_open() const { return (file != NULL); }
		gzfilebuf* open(const char* name, std::ios_base::openmode mode);
		gzfilebuf* attach(int fd, std::ios_base::openmode mode);
		gzfilebuf* close();

	protected:
		bool open_mode(std::ios_base::openmode mode, char* c_mode) const;
		virtual std::streamsize showmanyc();
		virtual int_type underflow();
		virtual int_type overflow(int_type c = traits_type::eof());
		virtual std::streambuf* setbuf(char_type* p, std::streamsize n);
		virtual int sync();
		virtual pos_type seekoff(off_type off, std::ios_base::seekdir way, std::ios_base::openmode mode = std::ios_base::in|std::ios_base::out);
		virtual pos_type seekpos(pos_type sp, std::ios_base::openmode mode = std::ios_base::in|std::ios_base::out);

//
// Some future enhancements
//
//  virtual int_type uflow();
//  virtual int_type pbackfail(int_type c = traits_type::eof());
//  virtual pos_type
//  seekoff(off_type off,
//          std::ios_base::seekdir way,
//          std::ios_base::openmode mode = std::ios_base::in|std::ios_base::out);
//  virtual pos_type
//  seekpos(pos_type sp,
//          std::ios_base::openmode mode = std::ios_base::in|std::ios_base::out);

	private:
		// Private methods
		void enable_buffer();
		void disable_buffer();
		
		// Attributes
		gzFile file;
		std::ios_base::openmode io_mode;
		bool own_fd;
		char_type* buffer;
		std::streamsize buffer_size;
		bool own_buffer;
};

/*****************************************************************************/

class gzifstream : public std::istream
{
	public:
		// Constructor and destructor
		gzifstream();
		explicit gzifstream(const char* name, std::ios_base::openmode mode = std::ios_base::in);
		explicit gzifstream(int fd, std::ios_base::openmode mode = std::ios_base::in);
		
		// Methods and functions
		gzfilebuf* rdbuf() const { return const_cast<gzfilebuf*>(&sb); }
		bool is_open() { return sb.is_open(); }
		void open(const char* name, std::ios_base::openmode mode = std::ios_base::in);
		void attach(int fd, std::ios_base::openmode mode = std::ios_base::in);
		void close();
	private:
		gzfilebuf sb;
};

/*****************************************************************************/
class gzofstream : public std::ostream
{
	public:
		// Constructors and destructor
		gzofstream();
		explicit gzofstream(const char* name, std::ios_base::openmode mode = std::ios_base::out);
		explicit gzofstream(int fd, std::ios_base::openmode mode = std::ios_base::out);
		gzfilebuf* rdbuf() const { return const_cast<gzfilebuf*>(&sb); }
		bool is_open() { return sb.is_open(); }
		void open(const char* name, std::ios_base::openmode mode = std::ios_base::out);
		void attach(int fd, std::ios_base::openmode mode = std::ios_base::out);
		void close();
	private:
		gzfilebuf sb;
};

/*****************************************************************************/

template<typename T1, typename T2>
class gzomanip2
{
	public:
		// Allows insertor to peek at internals
		template <typename Ta, typename Tb>
		friend gzofstream& operator<<(gzofstream&, const gzomanip2<Ta,Tb>&);

		// Constructor
		gzomanip2(gzofstream& (*f)(gzofstream&, T1, T2), T1 v1, T2 v2);
	private:
		// Underlying manipulator function
		gzofstream& (*func)(gzofstream&, T1, T2);
		
		// Arguments for manipulator function
		T1 val1;
		T2 val2;
};

/*****************************************************************************/

// Manipulator function thunks through to stream buffer
inline gzofstream&
setcompression(gzofstream &gzs, int l, int s = Z_DEFAULT_STRATEGY)
{
	(gzs.rdbuf())->setcompression(l, s);
	return gzs;
}

// Manipulator constructor stores arguments
template<typename T1, typename T2>
inline
gzomanip2<T1,T2>::gzomanip2(gzofstream &(*f)(gzofstream &, T1, T2), T1 v1, T2 v2) : func(f), val1(v1), val2(v2)
{
}

// Insertor applies underlying manipulator function to stream
template<typename T1, typename T2>
inline gzofstream&
operator<<(gzofstream& s, const gzomanip2<T1,T2>& m)
{
	return (*m.func)(s, m.val1, m.val2);
}

// Insert this onto stream to simplify setting of compression level
inline gzomanip2<int,int>
setcompression(int l, int s = Z_DEFAULT_STRATEGY)
{
	return gzomanip2<int,int>(&setcompression, l, s);
}

#endif // ZFSTREAM_H
